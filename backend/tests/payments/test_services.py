import hashlib
import hmac
from decimal import Decimal

import pytest
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.payments.models import Payment
from apps.payments.services import PaymentService
from apps.products.models import Category, Inventory, Product
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
def completed_sale(db, cashier):
    category = Category.objects.create(name='Bebidas')
    product = Product.objects.create(
        category=category, name='Coca Cola', sku='CC-500', price=Decimal('10.00')
    )
    Inventory.objects.create(product=product, quantity=100)
    return SaleService.create_sale(
        cashier=cashier,
        items=[{'product_id': product.id, 'quantity': 1}],
    )


# ── Process payment ───────────────────────────────────────────────────────────

class TestProcessPayment:

    def test_cash_payment_is_immediately_paid(self, db, cashier, completed_sale):
        payment, created = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='cash',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        assert payment.status == Payment.Status.PAID
        assert created is True

    def test_yape_payment_starts_pending(self, db, cashier, completed_sale):
        payment, created = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        assert payment.status == Payment.Status.PENDING
        assert created is True

    def test_plin_payment_starts_pending(self, db, cashier, completed_sale):
        payment, created = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='plin',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        assert payment.status == Payment.Status.PENDING

    def test_card_payment_starts_pending(self, db, cashier, completed_sale):
        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='card',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        assert payment.status == Payment.Status.PENDING

    def test_idempotency_returns_existing_payment(self, db, cashier, completed_sale):
        payment1, created1 = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='cash',
            amount=completed_sale.total,
            idempotency_key='key-idempotent',
            created_by=cashier,
        )
        payment2, created2 = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='cash',
            amount=completed_sale.total,
            idempotency_key='key-idempotent',
            created_by=cashier,
        )
        assert payment1.id == payment2.id
        assert created1 is True
        assert created2 is False
        assert Payment.objects.filter(idempotency_key='key-idempotent').count() == 1

    def test_amount_mismatch_raises(self, db, cashier, completed_sale):
        with pytest.raises(HttpError) as exc:
            PaymentService.process_payment(
                sale_id=completed_sale.id,
                method='cash',
                amount=Decimal('999.00'),
                idempotency_key='key-001',
                created_by=cashier,
            )
        assert exc.value.status_code == 422

    def test_invalid_method_raises(self, db, cashier, completed_sale):
        with pytest.raises(HttpError) as exc:
            PaymentService.process_payment(
                sale_id=completed_sale.id,
                method='bitcoin',
                amount=completed_sale.total,
                idempotency_key='key-001',
                created_by=cashier,
            )
        assert exc.value.status_code == 400

    def test_nonexistent_sale_raises(self, db, cashier):
        import uuid
        with pytest.raises(HttpError) as exc:
            PaymentService.process_payment(
                sale_id=uuid.uuid4(),
                method='cash',
                amount=Decimal('10.00'),
                idempotency_key='key-001',
                created_by=cashier,
            )
        assert exc.value.status_code == 404

    def test_double_payment_on_same_sale_raises(self, db, cashier, completed_sale):
        PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='cash',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        with pytest.raises(HttpError) as exc:
            PaymentService.process_payment(
                sale_id=completed_sale.id,
                method='cash',
                amount=completed_sale.total,
                idempotency_key='key-002',
                created_by=cashier,
            )
        assert exc.value.status_code == 409


# ── Webhook handling ──────────────────────────────────────────────────────────

class TestWebhookHandling:

    def test_webhook_marks_payment_as_paid(self, db, cashier, completed_sale):
        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        updated = PaymentService.handle_webhook(
            provider='yape',
            external_id='key-001',
            provider_ref='YAPE-TXN-001',
            status='paid',
        )
        assert updated.status == Payment.Status.PAID
        assert updated.provider_ref == 'YAPE-TXN-001'

    def test_webhook_marks_payment_as_failed(self, db, cashier, completed_sale):
        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        updated = PaymentService.handle_webhook(
            provider='yape',
            external_id='key-001',
            provider_ref='YAPE-TXN-001',
            status='failed',
        )
        assert updated.status == Payment.Status.FAILED

    def test_duplicate_webhook_is_ignored(self, db, cashier, completed_sale):
        PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        PaymentService.handle_webhook(
            provider='yape',
            external_id='key-001',
            provider_ref='YAPE-TXN-001',
            status='paid',
        )
        # Same provider_ref — should not raise, just return existing
        result = PaymentService.handle_webhook(
            provider='yape',
            external_id='key-001',
            provider_ref='YAPE-TXN-001',
            status='paid',
        )
        assert result.provider_ref == 'YAPE-TXN-001'
        assert Payment.objects.filter(provider_ref='YAPE-TXN-001').count() == 1

    def test_webhook_unknown_external_id_raises(self, db):
        with pytest.raises(HttpError) as exc:
            PaymentService.handle_webhook(
                provider='yape',
                external_id='nonexistent-key',
                provider_ref='YAPE-TXN-999',
                status='paid',
            )
        assert exc.value.status_code == 404


# ── Webhook signature ─────────────────────────────────────────────────────────

class TestWebhookSignature:

    def test_valid_signature_passes(self, settings):
        settings.WEBHOOK_SECRET_KEY = 'test-secret'
        payload = b'{"status": "paid"}'
        mac = hmac.new(b'test-secret', payload, hashlib.sha256)
        signature = 'sha256=' + mac.hexdigest()
        assert PaymentService.validate_webhook_signature(payload, signature) is True

    def test_invalid_signature_fails(self, settings):
        settings.WEBHOOK_SECRET_KEY = 'test-secret'
        payload = b'{"status": "paid"}'
        assert PaymentService.validate_webhook_signature(payload, 'sha256=invalid') is False

    def test_missing_secret_fails(self, settings):
        settings.WEBHOOK_SECRET_KEY = ''
        payload = b'{"status": "paid"}'
        assert PaymentService.validate_webhook_signature(payload, 'sha256=anything') is False


# ── Reconciliation ────────────────────────────────────────────────────────────

class TestReconciliation:

    def test_reconcile_marks_stale_pending_as_failed(self, db, cashier, completed_sale):
        from datetime import timedelta

        from django.utils import timezone

        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        # Manually backdate the payment to simulate staleness
        Payment.objects.filter(id=payment.id).update(
            created_at=timezone.now() - timedelta(minutes=60)
        )

        count = PaymentService.reconcile_stale_payments()
        assert count == 1
        payment.refresh_from_db()
        assert payment.status == Payment.Status.FAILED

    def test_reconcile_does_not_affect_paid_payments(self, db, cashier, completed_sale):
        from datetime import timedelta

        from django.utils import timezone

        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='cash',
            amount=completed_sale.total,
            idempotency_key='key-001',
            created_by=cashier,
        )
        Payment.objects.filter(id=payment.id).update(
            created_at=timezone.now() - timedelta(minutes=60)
        )

        count = PaymentService.reconcile_stale_payments()
        assert count == 0
        payment.refresh_from_db()
        assert payment.status == Payment.Status.PAID
