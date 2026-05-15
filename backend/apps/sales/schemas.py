import uuid
from decimal import Decimal
from datetime import datetime
from ninja import Schema


class SaleItemInput(Schema):
    product_id: uuid.UUID
    quantity: int


class SaleCreateInput(Schema):
    items: list[SaleItemInput]
    discount: Decimal = Decimal('0')


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
    created_at: datetime

    @staticmethod
    def from_orm(sale):
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
                for item in sale.items.select_related('product').all()
            ],
            created_at=sale.created_at,
        )


class SaleListOut(Schema):
    count: int
    results: list[SaleOut]
