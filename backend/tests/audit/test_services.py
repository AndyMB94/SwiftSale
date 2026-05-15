from decimal import Decimal

import pytest

from apps.audit.models import AuditLog
from apps.authentication.models import User
from apps.authentication.services import AuthService
from apps.billing.models import BillingSeries
from apps.billing.services import BillingService
from apps.products.models import Category, Inventory, Product
from apps.products.services import InventoryService, ProductService
from apps.sales.services import SaleService
from apps.users.services import UserService


@pytest.fixture
def admin(db):
    return User.objects.create_user(
        email='audit_admin@test.com',
        password='testpass123',
        full_name='Audit Admin',
        role=User.Role.ADMIN,
    )


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email='audit_cashier@test.com',
        password='testpass123',
        full_name='Audit Cashier',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def product_with_stock(db):
    cat = Category.objects.create(name='Audit Cat')
    product = Product.objects.create(
        category=cat, name='Audit Product', sku='AUD-001', price=Decimal('10.00')
    )
    Inventory.objects.create(product=product, quantity=50)
    return product


# ── login_failed ──────────────────────────────────────────────────────────────

class TestLoginFailedAudit:
    def test_failed_login_creates_audit_log(self, db):
        with pytest.raises(ValueError):
            AuthService.login(email='noexiste@test.com', password='wrong')

        log = AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED).first()
        assert log is not None
        assert log.metadata['email'] == 'noexiste@test.com'

    def test_successful_login_does_not_log(self, db, cashier):
        AuthService.login(email='audit_cashier@test.com', password='testpass123')
        assert not AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED).exists()


# ── price_change ──────────────────────────────────────────────────────────────

class TestPriceChangeAudit:
    def test_price_change_creates_audit_log(self, db, product_with_stock):
        ProductService.update_product(product_with_stock.id, price=Decimal('15.00'))

        log = AuditLog.objects.filter(action=AuditLog.Action.PRICE_CHANGE).first()
        assert log is not None
        assert log.metadata['old_price'] == '10.00'
        assert log.metadata['new_price'] == '15.00'
        assert log.metadata['sku'] == 'AUD-001'

    def test_no_price_change_does_not_log(self, db, product_with_stock):
        ProductService.update_product(product_with_stock.id, name='Renamed Product')
        assert not AuditLog.objects.filter(action=AuditLog.Action.PRICE_CHANGE).exists()


# ── stock_edit ────────────────────────────────────────────────────────────────

class TestStockEditAudit:
    def test_stock_adjustment_creates_audit_log(self, db, product_with_stock, admin):
        InventoryService.adjust_stock(
            product_id=product_with_stock.id,
            quantity_delta=10,
            reason='Manual top-up',
            created_by=admin,
        )

        log = AuditLog.objects.filter(action=AuditLog.Action.STOCK_EDIT).first()
        assert log is not None
        assert log.metadata['quantity_delta'] == 10
        assert log.metadata['reason'] == 'Manual top-up'
        assert log.actor == admin


# ── sale_cancelled ────────────────────────────────────────────────────────────

class TestSaleCancelledAudit:
    def test_cancelled_sale_creates_audit_log(self, db, cashier, product_with_stock):
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_with_stock.id, 'quantity': 1}],
        )
        SaleService.cancel_sale(sale_id=sale.id, cancelled_by=cashier)

        log = AuditLog.objects.filter(action=AuditLog.Action.SALE_CANCELLED).first()
        assert log is not None
        assert log.target_id == str(sale.id)
        assert log.actor == cashier


# ── document_voided ───────────────────────────────────────────────────────────

class TestDocumentVoidedAudit:
    def test_voided_document_creates_audit_log(self, db, cashier, product_with_stock):
        BillingSeries.objects.create(series='B003', document_type='boleta', last_correlativo=0)
        sale = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product_with_stock.id, 'quantity': 1}],
        )
        doc = BillingService.issue_document(
            sale_id=sale.id,
            series_code='B003',
            document_type='boleta',
            customer_name='Cliente',
            customer_document_type='DNI',
            customer_document_number='12345678',
            customer_address='',
            items=[{'description': 'Audit Product', 'quantity': 1, 'unit_price': Decimal('10.00')}],
        )
        BillingService.void_document(document_id=doc.id, reason='Error de prueba')

        log = AuditLog.objects.filter(action=AuditLog.Action.DOCUMENT_VOIDED).first()
        assert log is not None
        assert log.metadata['full_number'] == doc.full_number
        assert log.metadata['reason'] == 'Error de prueba'


# ── user_deactivated ──────────────────────────────────────────────────────────

class TestUserDeactivatedAudit:
    def test_deactivating_user_creates_audit_log(self, db, cashier):
        UserService.update_user(user_id=cashier.id, full_name=None, role=None, is_active=False)

        log = AuditLog.objects.filter(action=AuditLog.Action.USER_DEACTIVATED).first()
        assert log is not None
        assert log.target_id == str(cashier.id)
        assert log.metadata['email'] == cashier.email

    def test_reactivating_user_does_not_log_deactivation(self, db, cashier):
        cashier.is_active = False
        cashier.save()
        UserService.update_user(user_id=cashier.id, full_name=None, role=None, is_active=True)

        assert not AuditLog.objects.filter(action=AuditLog.Action.USER_DEACTIVATED).exists()


# ── log_action error resilience ───────────────────────────────────────────────

class TestLogActionResilience:
    def test_log_action_does_not_raise_on_invalid_data(self, db):
        from apps.audit.services import log_action
        # Should not raise even with edge case data
        log_action(action='price_change', target_type='product', target_id='nonexistent-id')
        assert AuditLog.objects.filter(action='price_change').exists()
