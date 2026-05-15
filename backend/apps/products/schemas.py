import uuid
from datetime import datetime
from decimal import Decimal

from ninja import Schema

# ── Category ────────────────────────────────────────────────────────────────

class CategoryCreateInput(Schema):
    name: str
    description: str = ''


class CategoryUpdateInput(Schema):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryOut(Schema):
    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    created_at: datetime


class CategoryListOut(Schema):
    count: int
    results: list[CategoryOut]


# ── Product ──────────────────────────────────────────────────────────────────

class ProductCreateInput(Schema):
    category_id: uuid.UUID
    name: str
    description: str = ''
    sku: str
    barcode: str | None = None
    price: Decimal


class ProductUpdateInput(Schema):
    category_id: uuid.UUID | None = None
    name: str | None = None
    description: str | None = None
    sku: str | None = None
    barcode: str | None = None
    price: Decimal | None = None
    is_active: bool | None = None


class ProductOut(Schema):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    name: str
    description: str
    sku: str
    barcode: str | None
    price: Decimal
    is_active: bool
    created_at: datetime

    @staticmethod
    def from_orm(product):
        return ProductOut(
            id=product.id,
            category_id=product.category_id,
            category_name=product.category.name,
            name=product.name,
            description=product.description,
            sku=product.sku,
            barcode=product.barcode,
            price=product.price,
            is_active=product.is_active,
            created_at=product.created_at,
        )


class ProductListOut(Schema):
    count: int
    results: list[ProductOut]


# ── Inventory ────────────────────────────────────────────────────────────────

class InventoryOut(Schema):
    product_id: uuid.UUID
    product_name: str
    sku: str
    quantity: int
    low_stock_threshold: int
    is_low_stock: bool
    updated_at: datetime


class InventoryAdjustInput(Schema):
    quantity_delta: int
    reason: str


class InventoryMovementOut(Schema):
    id: uuid.UUID
    movement_type: str
    quantity_delta: int
    quantity_after: int
    reason: str
    created_at: datetime
