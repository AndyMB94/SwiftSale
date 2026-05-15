from decimal import Decimal

import pytest
from ninja.errors import HttpError

from apps.products.models import Category, Inventory, InventoryMovement, Product
from apps.products.services import CategoryService, InventoryService, ProductService


@pytest.fixture
def category(db):
    return Category.objects.create(name="Bebidas", description="Refrescos y agua")


@pytest.fixture
def product(db, category):
    p = Product.objects.create(
        category=category,
        name="Coca Cola 500ml",
        sku="CC-500",
        barcode="7501055300427",
        price=Decimal("3.50"),
    )
    Inventory.objects.create(product=p, quantity=0)
    return p


@pytest.fixture
def admin_user(db):
    from apps.authentication.models import User

    return User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
        full_name="Admin Test",
        role=User.Role.ADMIN,
    )


# ── CategoryService ───────────────────────────────────────────────────────────


class TestCategoryService:
    def test_create_category(self, db):
        cat = CategoryService.create_category(
            name="Snacks", description="Papas y galletas"
        )
        assert cat.id is not None
        assert cat.name == "Snacks"
        assert cat.is_active is True

    def test_create_duplicate_category_raises(self, db, category):
        with pytest.raises(HttpError) as exc:
            CategoryService.create_category(name="bebidas")
        assert exc.value.status_code == 409

    def test_list_categories_excludes_inactive(self, db, category):
        category.is_active = False
        category.save()
        results = CategoryService.list_categories()
        assert category not in results

    def test_list_categories_include_inactive(self, db, category):
        category.is_active = False
        category.save()
        results = CategoryService.list_categories(include_inactive=True)
        assert category in results

    def test_get_category_not_found_raises(self, db):
        import uuid

        with pytest.raises(HttpError) as exc:
            CategoryService.get_category(uuid.uuid4())
        assert exc.value.status_code == 404

    def test_update_category(self, db, category):
        updated = CategoryService.update_category(
            category_id=category.id,
            name="Bebidas Frías",
            description=None,
            is_active=None,
        )
        assert updated.name == "Bebidas Frías"


# ── ProductService ────────────────────────────────────────────────────────────


class TestProductService:
    def test_create_product_creates_inventory(self, db, category):
        product = ProductService.create_product(
            category_id=category.id,
            name="Inca Kola 500ml",
            sku="IK-500",
            price=Decimal("3.50"),
        )
        assert Inventory.objects.filter(product=product).exists()
        assert product.inventory.quantity == 0

    def test_create_duplicate_sku_raises(self, db, product):
        with pytest.raises(HttpError) as exc:
            ProductService.create_product(
                category_id=product.category_id,
                name="Otro Producto",
                sku="CC-500",
                price=Decimal("2.00"),
            )
        assert exc.value.status_code == 409

    def test_create_duplicate_barcode_raises(self, db, product):
        with pytest.raises(HttpError) as exc:
            ProductService.create_product(
                category_id=product.category_id,
                name="Otro Producto",
                sku="OTRO-001",
                barcode="7501055300427",
                price=Decimal("2.00"),
            )
        assert exc.value.status_code == 409

    def test_soft_delete_deactivates_product(self, db, product):
        ProductService.soft_delete(product.id)
        product.refresh_from_db()
        assert product.is_active is False

    def test_soft_deleted_product_excluded_from_list(self, db, product):
        ProductService.soft_delete(product.id)
        results = ProductService.list_products()
        assert product not in results

    def test_get_product_not_found_raises(self, db):
        import uuid

        with pytest.raises(HttpError) as exc:
            ProductService.get_product(uuid.uuid4())
        assert exc.value.status_code == 404


# ── InventoryService ──────────────────────────────────────────────────────────


class TestInventoryService:
    def test_adjust_stock_increases_quantity(self, db, product, admin_user):
        InventoryService.adjust_stock(
            product_id=product.id,
            quantity_delta=50,
            reason="Initial stock",
            created_by=admin_user,
        )
        product.inventory.refresh_from_db()
        assert product.inventory.quantity == 50

    def test_adjust_stock_decreases_quantity(self, db, product, admin_user):
        product.inventory.quantity = 100
        product.inventory.save()
        InventoryService.adjust_stock(
            product_id=product.id,
            quantity_delta=-30,
            reason="Sale",
            created_by=admin_user,
        )
        product.inventory.refresh_from_db()
        assert product.inventory.quantity == 70

    def test_adjust_stock_below_zero_raises(self, db, product, admin_user):
        with pytest.raises(HttpError) as exc:
            InventoryService.adjust_stock(
                product_id=product.id,
                quantity_delta=-10,
                reason="Test",
                created_by=admin_user,
            )
        assert exc.value.status_code == 400

    def test_adjust_stock_creates_movement(self, db, product, admin_user):
        InventoryService.adjust_stock(
            product_id=product.id,
            quantity_delta=20,
            reason="Purchase",
            created_by=admin_user,
        )
        movement = InventoryMovement.objects.get(inventory=product.inventory)
        assert movement.quantity_delta == 20
        assert movement.quantity_after == 20
        assert movement.reason == "Purchase"
        assert movement.created_by == admin_user

    def test_low_stock_flag(self, db, product):
        product.inventory.quantity = 5
        product.inventory.low_stock_threshold = 10
        product.inventory.save()
        assert product.inventory.is_low_stock is True

    def test_not_low_stock(self, db, product):
        product.inventory.quantity = 50
        product.inventory.low_stock_threshold = 10
        product.inventory.save()
        assert product.inventory.is_low_stock is False

    def test_list_low_stock_only(self, db, product, category, admin_user):
        product.inventory.quantity = 3
        product.inventory.low_stock_threshold = 10
        product.inventory.save()

        normal_product = ProductService.create_product(
            category_id=category.id,
            name="Agua San Luis",
            sku="ASL-500",
            price=Decimal("1.50"),
        )
        normal_product.inventory.quantity = 100
        normal_product.inventory.save()

        low_stock_items = InventoryService.list_inventory(low_stock_only=True)
        ids = [i.product_id for i in low_stock_items]
        assert product.id in ids
        assert normal_product.id not in ids
