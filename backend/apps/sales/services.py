import uuid
from decimal import Decimal

from django.db import transaction
from ninja.errors import HttpError

from apps.products.models import Inventory, InventoryMovement

from .models import IGV_RATE, Sale, SaleItem


class SaleService:
    @staticmethod
    @transaction.atomic
    def create_sale(
        cashier, items: list[dict], discount: Decimal = Decimal("0")
    ) -> Sale:
        if not items:
            raise HttpError(400, "Sale must have at least one item")
        if discount < 0:
            raise HttpError(400, "Discount cannot be negative")

        product_ids = [item["product_id"] for item in items]

        inventories = {
            inv.product_id: inv
            for inv in Inventory.objects.select_for_update()
            .filter(
                product_id__in=product_ids,
                product__is_active=True,
            )
            .select_related("product")
        }

        for item in items:
            if item["product_id"] not in inventories:
                raise HttpError(
                    404, f"Product {item['product_id']} not found or inactive"
                )
            inv = inventories[item["product_id"]]
            if inv.quantity < item["quantity"]:
                raise HttpError(
                    422,
                    f"Insufficient stock for '{inv.product.name}': "
                    f"requested {item['quantity']}, available {inv.quantity}",
                )

        subtotal = Decimal("0")
        sale_items_data = []
        for item in items:
            inv = inventories[item["product_id"]]
            unit_price = inv.product.price
            item_subtotal = unit_price * item["quantity"]
            subtotal += item_subtotal
            sale_items_data.append(
                {
                    "inventory": inv,
                    "product": inv.product,
                    "quantity": item["quantity"],
                    "unit_price": unit_price,
                    "subtotal": item_subtotal,
                }
            )

        tax = (subtotal * IGV_RATE).quantize(Decimal("0.01"))
        total = (subtotal - discount + tax).quantize(Decimal("0.01"))

        sale = Sale.objects.create(
            cashier=cashier,
            status=Sale.Status.COMPLETED,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=total,
        )

        for data in sale_items_data:
            SaleItem.objects.create(
                sale=sale,
                product=data["product"],
                quantity=data["quantity"],
                unit_price=data["unit_price"],
                subtotal=data["subtotal"],
            )
            inv = data["inventory"]
            new_quantity = inv.quantity - data["quantity"]
            inv.quantity = new_quantity
            inv.save(update_fields=["quantity", "updated_at"])
            InventoryMovement.objects.create(
                inventory=inv,
                movement_type=InventoryMovement.MovementType.SALE,
                quantity_delta=-data["quantity"],
                quantity_after=new_quantity,
                reason=f"Sale {sale.id}",
                created_by=cashier,
            )

        return sale

    @staticmethod
    @transaction.atomic
    def cancel_sale(sale_id: uuid.UUID, cancelled_by) -> Sale:
        try:
            sale = Sale.objects.select_for_update().get(id=sale_id)
        except Sale.DoesNotExist:
            raise HttpError(404, "Sale not found")

        if sale.status == Sale.Status.CANCELLED:
            raise HttpError(409, "Sale is already cancelled")

        if sale.status == Sale.Status.COMPLETED:
            items = sale.items.select_related("product__inventory").all()
            for item in items:
                inv = Inventory.objects.select_for_update().get(product=item.product)
                new_quantity = inv.quantity + item.quantity
                inv.quantity = new_quantity
                inv.save(update_fields=["quantity", "updated_at"])
                InventoryMovement.objects.create(
                    inventory=inv,
                    movement_type=InventoryMovement.MovementType.RETURN,
                    quantity_delta=item.quantity,
                    quantity_after=new_quantity,
                    reason=f"Cancellation of sale {sale.id}",
                    created_by=cancelled_by,
                )

        sale.status = Sale.Status.CANCELLED
        sale.save(update_fields=["status", "updated_at"])

        from apps.audit.models import AuditLog
        from apps.audit.services import log_action

        log_action(
            action=AuditLog.Action.SALE_CANCELLED,
            target_type="sale",
            target_id=str(sale.id),
            actor=cancelled_by,
            metadata={"total": str(sale.total), "cashier_id": str(sale.cashier_id)},
        )

        return sale

    @staticmethod
    def get_sale(sale_id: uuid.UUID) -> Sale:
        try:
            return Sale.objects.select_related("cashier").get(id=sale_id)
        except Sale.DoesNotExist:
            raise HttpError(404, "Sale not found")

    @staticmethod
    def list_sales(status: str | None = None) -> list[Sale]:
        qs = Sale.objects.select_related("cashier").all()
        if status:
            qs = qs.filter(status=status)
        return list(qs)
