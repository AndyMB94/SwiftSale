import uuid
from datetime import datetime
from decimal import Decimal

from ninja import Schema


class SaleItemInput(Schema):
    product_id: uuid.UUID
    quantity: int


class SaleCreateInput(Schema):
    items: list[SaleItemInput]
    discount: Decimal = Decimal("0")


class PaymentSummary(Schema):
    id: uuid.UUID
    method: str
    amount: Decimal
    status: str
    created_at: datetime


class SaleItemOut(Schema):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class SaleOut(Schema):
    id: uuid.UUID
    cashier_id: uuid.UUID
    cashier_name: str
    status: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    items: list[SaleItemOut]
    payment: PaymentSummary | None
    created_at: datetime

    @staticmethod
    def from_orm(sale):
        payments = list(sale.payments.all())
        payment_data = (
            PaymentSummary(
                id=payments[0].id,
                method=payments[0].method,
                amount=payments[0].amount,
                status=payments[0].status,
                created_at=payments[0].created_at,
            )
            if payments
            else None
        )
        return SaleOut(
            id=sale.id,
            cashier_id=sale.cashier_id,
            cashier_name=sale.cashier.full_name,
            status=sale.status,
            subtotal=sale.subtotal,
            discount=sale.discount,
            tax=sale.tax,
            total=sale.total,
            items=[
                SaleItemOut(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    sku=item.product.sku,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
                for item in sale.items.select_related("product").all()
            ],
            payment=payment_data,
            created_at=sale.created_at,
        )


class SaleListItemOut(Schema):
    id: uuid.UUID
    cashier_name: str
    status: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    item_count: int
    payment: PaymentSummary | None
    created_at: datetime

    @staticmethod
    def from_orm(sale):
        payments = list(sale.payments.all())
        payment_data = (
            PaymentSummary(
                id=payments[0].id,
                method=payments[0].method,
                amount=payments[0].amount,
                status=payments[0].status,
                created_at=payments[0].created_at,
            )
            if payments
            else None
        )
        return SaleListItemOut(
            id=sale.id,
            cashier_name=sale.cashier.full_name,
            status=sale.status,
            subtotal=sale.subtotal,
            discount=sale.discount,
            tax=sale.tax,
            total=sale.total,
            item_count=sale.item_count,
            payment=payment_data,
            created_at=sale.created_at,
        )


class SaleListOut(Schema):
    count: int
    total_pages: int
    page: int
    page_size: int
    results: list[SaleListItemOut]
