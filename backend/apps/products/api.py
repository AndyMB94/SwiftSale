import uuid
from ninja import Router
from django.http import HttpRequest

from apps.authentication.security import cookie_auth
from core.permissions import require_admin, require_admin_or_supervisor
from .schemas import (
    CategoryCreateInput, CategoryUpdateInput, CategoryOut, CategoryListOut,
    ProductCreateInput, ProductUpdateInput, ProductOut, ProductListOut,
    InventoryOut, InventoryAdjustInput, InventoryMovementOut,
)
from .services import CategoryService, ProductService, InventoryService
from .models import Inventory

router = Router(tags=['Products'])


# ── Categories ───────────────────────────────────────────────────────────────

@router.get('/categories', response=CategoryListOut, auth=cookie_auth)
def list_categories(request: HttpRequest, include_inactive: bool = False):
    categories = CategoryService.list_categories(include_inactive=include_inactive)
    return CategoryListOut(count=len(categories), results=categories)


@router.post('/categories', response={201: CategoryOut}, auth=cookie_auth)
def create_category(request: HttpRequest, payload: CategoryCreateInput):
    require_admin_or_supervisor(request)
    category = CategoryService.create_category(
        name=payload.name, description=payload.description
    )
    return 201, category


@router.get('/categories/{category_id}', response=CategoryOut, auth=cookie_auth)
def get_category(request: HttpRequest, category_id: uuid.UUID):
    return CategoryService.get_category(category_id)


@router.patch('/categories/{category_id}', response=CategoryOut, auth=cookie_auth)
def update_category(request: HttpRequest, category_id: uuid.UUID, payload: CategoryUpdateInput):
    require_admin_or_supervisor(request)
    return CategoryService.update_category(
        category_id=category_id,
        name=payload.name,
        description=payload.description,
        is_active=payload.is_active,
    )


# ── Products ─────────────────────────────────────────────────────────────────

@router.get('/products', response=ProductListOut, auth=cookie_auth)
def list_products(
    request: HttpRequest,
    include_inactive: bool = False,
    category_id: uuid.UUID | None = None,
):
    products = ProductService.list_products(
        include_inactive=include_inactive, category_id=category_id
    )
    return ProductListOut(
        count=len(products),
        results=[ProductOut.from_orm(p) for p in products],
    )


@router.post('/products', response={201: ProductOut}, auth=cookie_auth)
def create_product(request: HttpRequest, payload: ProductCreateInput):
    require_admin_or_supervisor(request)
    product = ProductService.create_product(
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        sku=payload.sku,
        barcode=payload.barcode,
        price=payload.price,
    )
    return 201, ProductOut.from_orm(product)


@router.get('/products/{product_id}', response=ProductOut, auth=cookie_auth)
def get_product(request: HttpRequest, product_id: uuid.UUID):
    return ProductOut.from_orm(ProductService.get_product(product_id))


@router.patch('/products/{product_id}', response=ProductOut, auth=cookie_auth)
def update_product(request: HttpRequest, product_id: uuid.UUID, payload: ProductUpdateInput):
    require_admin_or_supervisor(request)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    return ProductOut.from_orm(ProductService.update_product(product_id, **data))


@router.delete('/products/{product_id}', response={204: None}, auth=cookie_auth)
def delete_product(request: HttpRequest, product_id: uuid.UUID):
    require_admin(request)
    ProductService.soft_delete(product_id)
    return 204, None


# ── Inventory ─────────────────────────────────────────────────────────────────

@router.get('/inventory', response=list[InventoryOut], auth=cookie_auth)
def list_inventory(request: HttpRequest, low_stock_only: bool = False):
    items = InventoryService.list_inventory(low_stock_only=low_stock_only)
    return [
        InventoryOut(
            product_id=inv.product_id,
            product_name=inv.product.name,
            sku=inv.product.sku,
            quantity=inv.quantity,
            low_stock_threshold=inv.low_stock_threshold,
            is_low_stock=inv.is_low_stock,
            updated_at=inv.updated_at,
        )
        for inv in items
    ]


@router.get('/inventory/{product_id}', response=InventoryOut, auth=cookie_auth)
def get_inventory(request: HttpRequest, product_id: uuid.UUID):
    inv = InventoryService.get_inventory(product_id)
    return InventoryOut(
        product_id=inv.product_id,
        product_name=inv.product.name,
        sku=inv.product.sku,
        quantity=inv.quantity,
        low_stock_threshold=inv.low_stock_threshold,
        is_low_stock=inv.is_low_stock,
        updated_at=inv.updated_at,
    )


@router.post('/inventory/{product_id}/adjust', response=InventoryOut, auth=cookie_auth)
def adjust_inventory(request: HttpRequest, product_id: uuid.UUID, payload: InventoryAdjustInput):
    require_admin_or_supervisor(request)
    inv = InventoryService.adjust_stock(
        product_id=product_id,
        quantity_delta=payload.quantity_delta,
        reason=payload.reason,
        created_by=request.auth,
    )
    return InventoryOut(
        product_id=inv.product_id,
        product_name=inv.product.name,
        sku=inv.product.sku,
        quantity=inv.quantity,
        low_stock_threshold=inv.low_stock_threshold,
        is_low_stock=inv.is_low_stock,
        updated_at=inv.updated_at,
    )


@router.get('/inventory/{product_id}/movements', response=list[InventoryMovementOut], auth=cookie_auth)
def get_movements(request: HttpRequest, product_id: uuid.UUID):
    require_admin_or_supervisor(request)
    return InventoryService.get_movements(product_id)
