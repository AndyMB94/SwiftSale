import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.authentication.models import User
from apps.products.models import Category, Product, Inventory
from apps.sales.services import SaleService
from apps.payments.models import Payment
from apps.payments.services import PaymentService
from apps.billing.models import BillingSeries, BillingDocument
from apps.billing.services import BillingService


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email='notif_cashier@test.com',
        password='testpass123',
        full_name='Notif Cashier',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def completed_sale(db, cashier):
    category = Category.objects.create(name='Bebidas Notif')
    product = Product.objects.create(
        category=category, name='Inca Kola 500ml', sku='IK-500', price=Decimal('3.00')
    )
    Inventory.objects.create(product=product, quantity=50)
    return SaleService.create_sale(
        cashier=cashier,
        items=[{'product_id': product.id, 'quantity': 2}],
    )


@pytest.fixture
def boleta_series(db):
    return BillingSeries.objects.create(
        series='B002', document_type='boleta', last_correlativo=0
    )


# ── PDF Builder ───────────────────────────────────────────────────────────────

class TestPdfBuilder:
    def test_generates_valid_pdf_bytes(self):
        from apps.billing.pdf_builder import build_receipt_pdf

        pdf = build_receipt_pdf(
            full_number='B002-00000001',
            document_type='boleta',
            issue_date='2026-05-15',
            company_name='SwiftSale SAC',
            company_ruc='20000000001',
            company_address='Lima, Peru',
            customer_name='Juan Perez',
            customer_document_type='DNI',
            customer_document_number='12345678',
            items=[{
                'description': 'Inca Kola 500ml',
                'quantity': 2,
                'unit_price': Decimal('3.00'),
                'subtotal': Decimal('6.00'),
            }],
            subtotal=Decimal('6.00'),
            tax=Decimal('1.08'),
            discount=Decimal('0.00'),
            total=Decimal('7.08'),
        )

        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
        # PDF files start with %PDF
        assert pdf[:4] == b'%PDF'

    def test_pdf_has_reasonable_size(self):
        from apps.billing.pdf_builder import build_receipt_pdf

        pdf = build_receipt_pdf(
            full_number='B002-00000099',
            document_type='boleta',
            issue_date='2026-05-15',
            company_name='SwiftSale SAC',
            company_ruc='20000000001',
            company_address='Lima, Peru',
            customer_name='Maria Lopez',
            customer_document_type='DNI',
            customer_document_number='87654321',
            items=[{
                'description': 'Producto Test',
                'quantity': 1,
                'unit_price': Decimal('10.00'),
                'subtotal': Decimal('10.00'),
            }],
            subtotal=Decimal('10.00'),
            tax=Decimal('1.80'),
            discount=Decimal('0.00'),
            total=Decimal('11.80'),
        )
        # ReportLab compresses content streams — check size instead of raw bytes
        assert pdf[:4] == b'%PDF'
        assert len(pdf) > 1000


# ── generate_and_send_receipt task ────────────────────────────────────────────

class TestGenerateAndSendReceiptTask:
    def test_task_pushes_websocket_notification(self, db, completed_sale, boleta_series):
        doc = BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='B002',
            document_type='boleta',
            customer_name='Cliente Test',
            customer_document_type='DNI',
            customer_document_number='12345678',
            customer_address='',
            items=[{
                'description': 'Inca Kola 500ml',
                'quantity': 2,
                'unit_price': Decimal('3.00'),
            }],
        )

        with patch('apps.billing.tasks._push_receipt_ready') as mock_push:
            from apps.billing.tasks import generate_and_send_receipt
            generate_and_send_receipt(str(doc.id))

            mock_push.assert_called_once()
            pushed_doc = mock_push.call_args[0][0]
            assert pushed_doc.id == doc.id
            assert pushed_doc.full_number == 'B002-00000001'

    def test_task_skips_gracefully_for_missing_document(self, db):
        import uuid
        from apps.billing.tasks import generate_and_send_receipt
        # Should not raise
        generate_and_send_receipt(str(uuid.uuid4()))


# ── notify_payment_result task ────────────────────────────────────────────────

class TestNotifyPaymentResultTask:
    def test_pushes_payment_confirmed_event(self, db, completed_sale):
        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='test-idem-notif-1',
            created_by=completed_sale.cashier,
        )

        with patch('apps.payments.tasks._push') as mock_push:
            from apps.payments.tasks import notify_payment_result
            payment.status = Payment.Status.PAID
            payment.save()
            notify_payment_result(str(payment.id))

            mock_push.assert_called_once()
            payload = mock_push.call_args[1]['payload']
            assert payload['event'] == 'payment.confirmed'
            assert payload['payment_id'] == str(payment.id)

    def test_pushes_payment_failed_event(self, db, completed_sale):
        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='card',
            amount=completed_sale.total,
            idempotency_key='test-idem-notif-2',
            created_by=completed_sale.cashier,
        )

        with patch('apps.payments.tasks._push') as mock_push:
            from apps.payments.tasks import notify_payment_result
            payment.status = Payment.Status.FAILED
            payment.save()
            notify_payment_result(str(payment.id))

            payload = mock_push.call_args[1]['payload']
            assert payload['event'] == 'payment.failed'

    def test_task_skips_gracefully_for_missing_payment(self, db):
        import uuid
        from apps.payments.tasks import notify_payment_result
        notify_payment_result(str(uuid.uuid4()))


# ── notify_low_stock task ──────────────────────────────────────────────────────

class TestNotifyLowStockTask:
    def test_pushes_low_stock_event(self, db):
        category = Category.objects.create(name='LowStockCat')
        product = Product.objects.create(
            category=category, name='Item Escaso', sku='ESCASO-001', price=Decimal('5.00')
        )
        Inventory.objects.create(product=product, quantity=3, low_stock_threshold=10)

        with patch('apps.products.tasks._push_low_stock') as mock_push:
            from apps.products.tasks import notify_low_stock
            notify_low_stock(product.id, 3)

            mock_push.assert_called_once()
            args = mock_push.call_args[0]
            assert args[0].id == product.id
            assert args[1] == 3

    def test_task_skips_gracefully_for_missing_product(self, db):
        from apps.products.tasks import notify_low_stock
        notify_low_stock(999999, 0)


# ── reconcile_stale_payments_task ─────────────────────────────────────────────

class TestReconcileStaleTask:
    def test_reconcile_task_returns_count(self, db, completed_sale):
        from django.utils import timezone
        from datetime import timedelta

        payment, _ = PaymentService.process_payment(
            sale_id=completed_sale.id,
            method='yape',
            amount=completed_sale.total,
            idempotency_key='test-stale-notif',
            created_by=completed_sale.cashier,
        )
        Payment.objects.filter(id=payment.id).update(
            created_at=timezone.now() - timedelta(hours=1)
        )

        from apps.payments.tasks import reconcile_stale_payments_task
        count = reconcile_stale_payments_task()
        assert count == 1
