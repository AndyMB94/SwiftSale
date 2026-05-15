import uuid
from decimal import Decimal
from django.db import transaction
from ninja.errors import HttpError

from .models import Category, Product, Inventory, InventoryMovement


def _enqueue_low_stock(product_id, quantity: int):
    try:
        from .tasks import notify_low_stock
        notify_low_stock.delay(product_id, quantity)
    except Exception:
        pass


class CategoryService:

    @staticmethod
    def list_categories(include_inactive: bool = False) -> list[Category]:
        qs = Category.objects.all()
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return list(qs)

    @staticmethod
    def get_category(category_id: uuid.UUID) -> Category:
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise HttpError(404, 'Category not found')

    @staticmethod
    def create_category(name: str, description: str = '') -> Category:
        if Category.objects.filter(name__iexact=name).exists():
            raise HttpError(409, 'A category with this name already exists')
        return Category.objects.create(name=name, description=description)

    @staticmethod
    def update_category(
        category_id: uuid.UUID,
        name: str | None,
        description: str | None,
        is_active: bool | None,
    ) -> Category:
        category = CategoryService.get_category(category_id)
        if name is not None:
            if Category.objects.filter(name__iexact=name).exclude(id=category_id).exists():
                raise HttpError(409, 'A category with this name already exists')
            category.name = name
        if description is not None:
            category.description = description
        if is_active is not None:
            category.is_active = is_active
        category.save()
        return category


class ProductService:

    @staticmethod
    def list_products(include_inactive: bool = False, category_id: uuid.UUID | None = None):
        qs = Product.objects.select_related('category').all()
        if not include_inactive:
            qs = qs.filter(is_active=True)
        if category_id:
            qs = qs.filter(category_id=category_id)
        return list(qs)

    @staticmethod
    def get_product(product_id: uuid.UUID) -> Product:
        try:
            return Product.objects.select_related('category').get(id=product_id)
        except Product.DoesNotExist:
            raise HttpError(404, 'Product not found')

    @staticmethod
    @transaction.atomic
    def create_product(
        category_id: uuid.UUID,
        name: str,
        sku: str,
        price: Decimal,
        description: str = '',
        barcode: str | None = None,
    ) -> Product:
        if Product.objects.filter(sku__iexact=sku).exists():
            raise HttpError(409, 'A product with this SKU already exists')
        if barcode and Product.objects.filter(barcode=barcode).exists():
            raise HttpError(409, 'A product with this barcode already exists')
        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise HttpError(404, 'Category not found')

        product = Product.objects.create(
            category=category,
            name=name,
            description=description,
            sku=sku,
            barcode=barcode,
            price=price,
        )
        Inventory.objects.create(product=product, quantity=0)
        return product

    @staticmethod
    @transaction.atomic
    def update_product(product_id: uuid.UUID, **kwargs) -> Product:
        product = ProductService.get_product(product_id)
        sku = kwargs.get('sku')
        barcode = kwargs.get('barcode')
        if sku and Product.objects.filter(sku__iexact=sku).exclude(id=product_id).exists():
            raise HttpError(409, 'A product with this SKU already exists')
        if barcode and Product.objects.filter(barcode=barcode).exclude(id=product_id).exists():
            raise HttpError(409, 'A product with this barcode already exists')

        category_id = kwargs.pop('category_id', None)
        if category_id:
            try:
                product.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                raise HttpError(404, 'Category not found')

        for field, value in kwargs.items():
            if value is not None:
                setattr(product, field, value)
        product.save()
        return product

    @staticmethod
    def soft_delete(product_id: uuid.UUID) -> Product:
        product = ProductService.get_product(product_id)
        product.is_active = False
        product.save(update_fields=['is_active'])
        return product


class InventoryService:

    @staticmethod
    def get_inventory(product_id: uuid.UUID) -> Inventory:
        try:
            return Inventory.objects.select_related('product').get(product_id=product_id)
        except Inventory.DoesNotExist:
            raise HttpError(404, 'Inventory not found')

    @staticmethod
    def list_inventory(low_stock_only: bool = False):
        qs = Inventory.objects.select_related('product').filter(product__is_active=True)
        if low_stock_only:
            from django.db.models import F
            qs = qs.filter(quantity__lte=F('low_stock_threshold'))
        return list(qs)

    @staticmethod
    @transaction.atomic
    def adjust_stock(
        product_id: uuid.UUID,
        quantity_delta: int,
        reason: str,
        created_by,
        movement_type: str = InventoryMovement.MovementType.ADJUSTMENT,
    ) -> Inventory:
        inventory = Inventory.objects.select_for_update().get(product_id=product_id)
        new_quantity = inventory.quantity + quantity_delta
        if new_quantity < 0:
            raise HttpError(400, 'Insufficient stock')
        inventory.quantity = new_quantity
        inventory.save(update_fields=['quantity', 'updated_at'])
        InventoryMovement.objects.create(
            inventory=inventory,
            movement_type=movement_type,
            quantity_delta=quantity_delta,
            quantity_after=new_quantity,
            reason=reason,
            created_by=created_by,
        )

        if inventory.is_low_stock:
            pid, qty = product_id, new_quantity
            transaction.on_commit(lambda: _enqueue_low_stock(pid, qty))

        return inventory

    @staticmethod
    def get_movements(product_id: uuid.UUID) -> list[InventoryMovement]:
        try:
            inventory = Inventory.objects.get(product_id=product_id)
        except Inventory.DoesNotExist:
            raise HttpError(404, 'Inventory not found')
        return list(InventoryMovement.objects.filter(inventory=inventory))
