import pytest
from decimal import Decimal
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.products.models import Category, Product, Inventory, InventoryMovement
from apps.sales.models import Sale, SaleItem
from apps.sales.services import SaleService


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email='cashier@test.com',
        password='testpass123',
        full_name='Test Cashier',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def supervisor(db):
    return User.objects.create_user(
        email='supervisor@test.com',
        password='testpass123',
        full_name='Test Supervisor',
        role=User.Role.SUPERVISOR,
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name='Bebidas')


@pytest.fixture
def product_a(db, category):
    p = Product.objects.create(
        category=category, name='Coca Cola 500ml', sku='CC-500', price=Decimal('3.50')
    )
    Inventory.objects.create(product=p, quantity=100)
    return p


@pytest.fixture
def product_b(db, category):
    p = Product.objects.create(
        category=category, name='Inca Kola 500ml', sku='IK-500', price=Decimal('3.50')
    )
    Inventory.objects.create(product=p, quantity=50)
    return p


# ── Create sale ───────────────────────────────────────────────────────────────

class TestCreateSale:

    def test_create_sale_returns_completed_status(self, db, cashier, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 2}],
        )
        assert sale.status == Sale.Status.COMPLETED

    def test_create_sale_deducts_inventory(self, db, cashier, product_a):
        SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 10}],
        )
        product_a.inventory.refresh_from_db()
        assert product_a.inventory.quantity == 90

    def test_create_sale_snapshot_unit_price(self, db, cashier, product_a):
        original_price = product_a.price
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 1}],
        )
        product_a.price = Decimal('99.00')
        product_a.save()
        item = sale.items.first()
        assert item.unit_price == original_price

    def test_create_sale_calculates_tax(self, db, cashier, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 2}],
        )
        expected_subtotal = Decimal('7.00')
        expected_tax = (expected_subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        assert sale.subtotal == expected_subtotal
        assert sale.tax == expected_tax

    def test_create_sale_applies_discount(self, db, cashier, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 2}],
            discount=Decimal('1.00'),
        )
        expected_subtotal = Decimal('7.00')
        expected_tax = (expected_subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        expected_total = expected_subtotal - Decimal('1.00') + expected_tax
        assert sale.discount == Decimal('1.00')
        assert sale.total == expected_total

    def test_create_sale_multiple_items(self, db, cashier, product_a, product_b):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[
                {'product_id': product_a.id, 'quantity': 2},
                {'product_id': product_b.id, 'quantity': 3},
            ],
        )
        assert sale.items.count() == 2
        assert sale.subtotal == Decimal('17.50')

    def test_create_sale_creates_inventory_movements(self, db, cashier, product_a):
        SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 5}],
        )
        movement = InventoryMovement.objects.get(inventory=product_a.inventory)
        assert movement.movement_type == InventoryMovement.MovementType.SALE
        assert movement.quantity_delta == -5
        assert movement.quantity_after == 95

    def test_create_sale_empty_items_raises(self, db, cashier):
        with pytest.raises(HttpError) as exc:
            SaleService.create_sale(cashier=cashier, items=[])
        assert exc.value.status_code == 400

    def test_create_sale_insufficient_stock_raises(self, db, cashier, product_a):
        with pytest.raises(HttpError) as exc:
            SaleService.create_sale(
                cashier=cashier,
                items=[{'product_id': product_a.id, 'quantity': 999}],
            )
        assert exc.value.status_code == 422

    def test_create_sale_inactive_product_raises(self, db, cashier, product_a):
        product_a.is_active = False
        product_a.save()
        with pytest.raises(HttpError) as exc:
            SaleService.create_sale(
                cashier=cashier,
                items=[{'product_id': product_a.id, 'quantity': 1}],
            )
        assert exc.value.status_code == 404

    def test_create_sale_negative_discount_raises(self, db, cashier, product_a):
        with pytest.raises(HttpError) as exc:
            SaleService.create_sale(
                cashier=cashier,
                items=[{'product_id': product_a.id, 'quantity': 1}],
                discount=Decimal('-5.00'),
            )
        assert exc.value.status_code == 400


# ── Cancel sale ───────────────────────────────────────────────────────────────

class TestCancelSale:

    def test_cancel_completed_sale_returns_stock(self, db, cashier, supervisor, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 10}],
        )
        product_a.inventory.refresh_from_db()
        assert product_a.inventory.quantity == 90

        SaleService.cancel_sale(sale.id, cancelled_by=supervisor)

        product_a.inventory.refresh_from_db()
        assert product_a.inventory.quantity == 100

    def test_cancel_sale_sets_cancelled_status(self, db, cashier, supervisor, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 1}],
        )
        cancelled = SaleService.cancel_sale(sale.id, cancelled_by=supervisor)
        assert cancelled.status == Sale.Status.CANCELLED

    def test_cancel_sale_creates_return_movements(self, db, cashier, supervisor, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 5}],
        )
        SaleService.cancel_sale(sale.id, cancelled_by=supervisor)
        movements = InventoryMovement.objects.filter(
            inventory=product_a.inventory,
            movement_type=InventoryMovement.MovementType.RETURN,
        )
        assert movements.count() == 1
        assert movements.first().quantity_delta == 5

    def test_cancel_already_cancelled_sale_raises(self, db, cashier, supervisor, product_a):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_a.id, 'quantity': 1}],
        )
        SaleService.cancel_sale(sale.id, cancelled_by=supervisor)
        with pytest.raises(HttpError) as exc:
            SaleService.cancel_sale(sale.id, cancelled_by=supervisor)
        assert exc.value.status_code == 409

    def test_cancel_nonexistent_sale_raises(self, db, supervisor):
        import uuid
        with pytest.raises(HttpError) as exc:
            SaleService.cancel_sale(uuid.uuid4(), cancelled_by=supervisor)
        assert exc.value.status_code == 404
