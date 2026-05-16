from decimal import Decimal

import pytest
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.payments.models import Payment
from apps.products.models import Category, Inventory, Product
from apps.sales.checkout import CheckoutService
from apps.sales.models import Sale


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email="cashier@test.com",
        password="testpass123",
        full_name="Test Cashier",
        role=User.Role.CASHIER,
    )


@pytest.fixture
def product(db):
    category = Category.objects.create(name="Bebidas")
    p = Product.objects.create(
        category=category,
        name="Coca Cola 500ml",
        sku="CC-500",
        price=Decimal("3.50"),
    )
    Inventory.objects.create(product=p, quantity=100)
    return p


class TestCheckoutService:
    def test_checkout_creates_sale_and_payment(self, db, cashier, product):
        sale, payment = CheckoutService.checkout(
            cashier=cashier,
            items=[{"product_id": product.id, "quantity": 2}],
            discount=Decimal("0"),
            method="cash",
            idempotency_key="key-001",
        )
        assert Sale.objects.filter(id=sale.id).exists()
        assert Payment.objects.filter(id=payment.id).exists()

    def test_checkout_cash_payment_is_immediately_paid(self, db, cashier, product):
        _, payment = CheckoutService.checkout(
            cashier=cashier,
            items=[{"product_id": product.id, "quantity": 1}],
            discount=Decimal("0"),
            method="cash",
            idempotency_key="key-001",
        )
        assert payment.status == Payment.Status.PAID

    def test_checkout_sale_is_completed(self, db, cashier, product):
        sale, _ = CheckoutService.checkout(
            cashier=cashier,
            items=[{"product_id": product.id, "quantity": 1}],
            discount=Decimal("0"),
            method="cash",
            idempotency_key="key-001",
        )
        assert sale.status == Sale.Status.COMPLETED

    def test_checkout_deducts_stock(self, db, cashier, product):
        CheckoutService.checkout(
            cashier=cashier,
            items=[{"product_id": product.id, "quantity": 10}],
            discount=Decimal("0"),
            method="cash",
            idempotency_key="key-001",
        )
        product.inventory.refresh_from_db()
        assert product.inventory.quantity == 90

    def test_checkout_payment_amount_matches_sale_total(self, db, cashier, product):
        sale, payment = CheckoutService.checkout(
            cashier=cashier,
            items=[{"product_id": product.id, "quantity": 2}],
            discount=Decimal("0"),
            method="cash",
            idempotency_key="key-001",
        )
        assert payment.amount == sale.total

    # ── Rollback tests (the key guarantee of Option B) ────────────────────────

    def test_checkout_invalid_method_rolls_back_sale(self, db, cashier, product):
        with pytest.raises(HttpError):
            CheckoutService.checkout(
                cashier=cashier,
                items=[{"product_id": product.id, "quantity": 1}],
                discount=Decimal("0"),
                method="bitcoin",  # invalid → payment fails
                idempotency_key="key-001",
            )
        assert Sale.objects.count() == 0

    def test_checkout_invalid_method_rolls_back_stock(self, db, cashier, product):
        with pytest.raises(HttpError):
            CheckoutService.checkout(
                cashier=cashier,
                items=[{"product_id": product.id, "quantity": 1}],
                discount=Decimal("0"),
                method="bitcoin",
                idempotency_key="key-001",
            )
        product.inventory.refresh_from_db()
        assert product.inventory.quantity == 100

    def test_checkout_insufficient_stock_raises_and_creates_nothing(
        self, db, cashier, product
    ):
        with pytest.raises(HttpError) as exc:
            CheckoutService.checkout(
                cashier=cashier,
                items=[{"product_id": product.id, "quantity": 999}],
                discount=Decimal("0"),
                method="cash",
                idempotency_key="key-001",
            )
        assert exc.value.status_code == 422
        assert Sale.objects.count() == 0
        assert Payment.objects.count() == 0

    def test_checkout_with_discount_applies_correctly(self, db, cashier, product):
        sale, payment = CheckoutService.checkout(
            cashier=cashier,
            items=[{"product_id": product.id, "quantity": 2}],
            discount=Decimal("1.00"),
            method="cash",
            idempotency_key="key-001",
        )
        subtotal = Decimal("7.00")
        tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
        expected_total = subtotal - Decimal("1.00") + tax
        assert sale.total == expected_total
        assert payment.amount == expected_total
