from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.billing.models import BillingDocument, BillingSeries
from apps.billing.ose_client import MockOseClient, OseResponse
from apps.billing.services import BillingService
from apps.products.models import Category, Inventory, Product
from apps.sales.services import SaleService


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email='billing_cashier@test.com',
        password='testpass123',
        full_name='Billing Cashier',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def boleta_series(db):
    return BillingSeries.objects.create(
        series='B001',
        document_type='boleta',
        last_correlativo=0,
    )


@pytest.fixture
def factura_series(db):
    return BillingSeries.objects.create(
        series='F001',
        document_type='factura',
        last_correlativo=0,
    )


@pytest.fixture
def completed_sale(db, cashier):
    category = Category.objects.create(name='Abarrotes')
    product = Product.objects.create(
        category=category,
        name='Agua San Luis 500ml',
        sku='AQ-500',
        price=Decimal('2.50'),
    )
    Inventory.objects.create(product=product, quantity=50)
    return SaleService.create_sale(
        cashier=cashier,
        items=[{'product_id': product.id, 'quantity': 2}],
    )


@pytest.fixture
def sample_items():
    return [
        {
            'description': 'Agua San Luis 500ml',
            'quantity': 2,
            'unit_price': Decimal('2.50'),
        }
    ]


# ── XML Builder ───────────────────────────────────────────────────────────────

class TestXmlBuilder:
    def test_builds_valid_xml(self):
        from apps.billing.xml_builder import build_invoice_xml

        xml = build_invoice_xml(
            full_number='B001-00000001',
            document_type='boleta',
            issue_date='2026-05-15',
            company_ruc='20000000001',
            company_name='SwiftSale SAC',
            company_address='Lima, Peru',
            customer_name='Juan Perez',
            customer_document_type='DNI',
            customer_document_number='12345678',
            subtotal=Decimal('4.24'),
            tax=Decimal('0.76'),
            discount=Decimal('0.00'),
            total=Decimal('5.00'),
            items=[{
                'description': 'Agua San Luis 500ml',
                'quantity': 2,
                'unit_price': Decimal('2.50'),
                'subtotal': Decimal('4.24'),
                'tax': Decimal('0.76'),
            }],
        )

        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml
        assert 'B001-00000001' in xml
        assert '20000000001' in xml
        assert 'Juan Perez' in xml
        assert 'IGV' in xml
        assert '2.1' in xml

    def test_factura_doc_type_code(self):
        from apps.billing.xml_builder import build_invoice_xml

        xml = build_invoice_xml(
            full_number='F001-00000001',
            document_type='factura',
            issue_date='2026-05-15',
            company_ruc='20000000001',
            company_name='SwiftSale SAC',
            company_address='Lima, Peru',
            customer_name='Empresa ABC SAC',
            customer_document_type='RUC',
            customer_document_number='20123456789',
            subtotal=Decimal('100.00'),
            tax=Decimal('18.00'),
            discount=Decimal('0.00'),
            total=Decimal('118.00'),
            items=[{
                'description': 'Producto Test',
                'quantity': 1,
                'unit_price': Decimal('100.00'),
                'subtotal': Decimal('100.00'),
                'tax': Decimal('18.00'),
            }],
        )

        # factura type code is '01'
        assert 'listID="0101"' in xml
        assert '01' in xml


# ── MockOseClient ─────────────────────────────────────────────────────────────

class TestMockOseClient:
    def test_always_accepts(self):
        client = MockOseClient()
        response = client.send_document(
            ruc='20000000001',
            full_number='B001-00000001',
            xml_content='<xml/>',
        )
        assert response.accepted is True
        assert response.response_code == '0'
        assert 'B001-00000001' in response.description

    def test_cdr_is_base64(self):
        import base64
        client = MockOseClient()
        response = client.send_document('20000000001', 'B001-00000001', '<xml/>')
        decoded = base64.b64decode(response.cdr_content).decode()
        assert 'B001-00000001' in decoded


# ── BillingService.issue_document ─────────────────────────────────────────────

class TestIssueDocument:
    def test_issue_boleta_success(self, db, completed_sale, boleta_series, sample_items):
        doc = BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='B001',
            document_type='boleta',
            customer_name='Juan Perez',
            customer_document_type='DNI',
            customer_document_number='12345678',
            customer_address='',
            items=sample_items,
        )

        assert doc.full_number == 'B001-00000001'
        assert doc.document_type == 'boleta'
        assert doc.status == BillingDocument.Status.ACCEPTED
        assert doc.subtotal == Decimal('5.00')
        assert doc.tax == Decimal('0.90')
        assert doc.total == Decimal('5.90')

    def test_issue_factura_success(self, db, completed_sale, factura_series, sample_items):
        doc = BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='F001',
            document_type='factura',
            customer_name='Empresa ABC SAC',
            customer_document_type='RUC',
            customer_document_number='20123456789',
            customer_address='Av. Lima 123',
            items=sample_items,
        )

        assert doc.full_number == 'F001-00000001'
        assert doc.document_type == 'factura'
        assert doc.status == BillingDocument.Status.ACCEPTED

    def test_correlativo_increments_sequentially(self, db, completed_sale, boleta_series, sample_items, cashier):
        Category.objects.get(name='Abarrotes')
        product = Product.objects.get(sku='AQ-500')

        doc1 = BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='B001',
            document_type='boleta',
            customer_name='Cliente Uno',
            customer_document_type='DNI',
            customer_document_number='11111111',
            customer_address='',
            items=sample_items,
        )

        # Create a second sale for the second document
        Inventory.objects.filter(product=product).update(quantity=50)
        sale2 = SaleService.create_sale(
            cashier=cashier,
            items=[{'product_id': product.id, 'quantity': 1}],
        )
        doc2 = BillingService.issue_document(
            sale_id=sale2.id,
            series_code='B001',
            document_type='boleta',
            customer_name='Cliente Dos',
            customer_document_type='DNI',
            customer_document_number='22222222',
            customer_address='',
            items=[{'description': 'Agua', 'quantity': 1, 'unit_price': Decimal('2.50')}],
        )

        assert doc1.full_number == 'B001-00000001'
        assert doc2.full_number == 'B001-00000002'

    def test_sale_not_found_raises_404(self, db, boleta_series, sample_items):
        import uuid
        with pytest.raises(HttpError) as exc:
            BillingService.issue_document(
                sale_id=uuid.uuid4(),
                series_code='B001',
                document_type='boleta',
                customer_name='Cliente',
                customer_document_type='DNI',
                customer_document_number='12345678',
                customer_address='',
                items=sample_items,
            )
        assert exc.value.status_code == 404

    def test_series_not_found_raises_404(self, db, completed_sale, sample_items):
        with pytest.raises(HttpError) as exc:
            BillingService.issue_document(
                sale_id=completed_sale.id,
                series_code='B999',
                document_type='boleta',
                customer_name='Cliente',
                customer_document_type='DNI',
                customer_document_number='12345678',
                customer_address='',
                items=sample_items,
            )
        assert exc.value.status_code == 404

    def test_duplicate_billing_for_sale_raises_409(self, db, completed_sale, boleta_series, sample_items):
        BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='B001',
            document_type='boleta',
            customer_name='Cliente',
            customer_document_type='DNI',
            customer_document_number='12345678',
            customer_address='',
            items=sample_items,
        )

        with pytest.raises(HttpError) as exc:
            BillingService.issue_document(
                sale_id=completed_sale.id,
                series_code='B001',
                document_type='boleta',
                customer_name='Cliente',
                customer_document_type='DNI',
                customer_document_number='12345678',
                customer_address='',
                items=sample_items,
            )
        assert exc.value.status_code == 409

    def test_ose_failure_marks_as_sent(self, db, completed_sale, boleta_series, sample_items):
        with patch('apps.billing.services.get_ose_client') as mock_get:
            mock_client = MagicMock()
            mock_client.send_document.side_effect = Exception('OSE timeout')
            mock_get.return_value = mock_client

            doc = BillingService.issue_document(
                sale_id=completed_sale.id,
                series_code='B001',
                document_type='boleta',
                customer_name='Cliente',
                customer_document_type='DNI',
                customer_document_number='12345678',
                customer_address='',
                items=sample_items,
            )

        assert doc.status == BillingDocument.Status.SENT

    def test_ose_rejection_marks_as_rejected(self, db, completed_sale, boleta_series, sample_items):
        with patch('apps.billing.services.get_ose_client') as mock_get:
            mock_client = MagicMock()
            mock_client.send_document.return_value = OseResponse(
                accepted=False,
                cdr_content='',
                response_code='2800',
                description='El numero de RUC no existe en los registros de la SUNAT',
            )
            mock_get.return_value = mock_client

            doc = BillingService.issue_document(
                sale_id=completed_sale.id,
                series_code='B001',
                document_type='boleta',
                customer_name='Cliente',
                customer_document_type='DNI',
                customer_document_number='12345678',
                customer_address='',
                items=sample_items,
            )

        assert doc.status == BillingDocument.Status.REJECTED
        assert doc.sunat_response_code == '2800'


# ── BillingService.void_document ──────────────────────────────────────────────

class TestVoidDocument:
    def test_void_accepted_document(self, db, completed_sale, boleta_series, sample_items):
        doc = BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='B001',
            document_type='boleta',
            customer_name='Cliente',
            customer_document_type='DNI',
            customer_document_number='12345678',
            customer_address='',
            items=sample_items,
        )
        assert doc.status == BillingDocument.Status.ACCEPTED

        voided = BillingService.void_document(document_id=doc.id, reason='Error en datos')
        assert voided.status == BillingDocument.Status.VOIDED
        assert voided.voided_at is not None

    def test_void_already_voided_raises_409(self, db, completed_sale, boleta_series, sample_items):
        doc = BillingService.issue_document(
            sale_id=completed_sale.id,
            series_code='B001',
            document_type='boleta',
            customer_name='Cliente',
            customer_document_type='DNI',
            customer_document_number='12345678',
            customer_address='',
            items=sample_items,
        )
        BillingService.void_document(document_id=doc.id, reason='Error')

        with pytest.raises(HttpError) as exc:
            BillingService.void_document(document_id=doc.id, reason='Error again')
        assert exc.value.status_code == 409

    def test_void_nonexistent_raises_404(self, db):
        import uuid
        with pytest.raises(HttpError) as exc:
            BillingService.void_document(document_id=uuid.uuid4(), reason='Error')
        assert exc.value.status_code == 404

    def test_void_rejected_document_raises_400(self, db, completed_sale, boleta_series, sample_items):
        with patch('apps.billing.services.get_ose_client') as mock_get:
            mock_client = MagicMock()
            mock_client.send_document.return_value = OseResponse(
                accepted=False, cdr_content='', response_code='2800', description='error'
            )
            mock_get.return_value = mock_client

            doc = BillingService.issue_document(
                sale_id=completed_sale.id,
                series_code='B001',
                document_type='boleta',
                customer_name='Cliente',
                customer_document_type='DNI',
                customer_document_number='12345678',
                customer_address='',
                items=sample_items,
            )

        assert doc.status == BillingDocument.Status.REJECTED
        with pytest.raises(HttpError) as exc:
            BillingService.void_document(document_id=doc.id, reason='Error')
        assert exc.value.status_code == 400


# ── Correlativo concurrency ────────────────────────────────────────────────────

class TestCorrelativoConcurrency:
    @pytest.mark.django_db(transaction=True)
    def test_concurrent_issue_produces_unique_numbers(self, boleta_series, cashier):
        """Two concurrent requests must get different correlativos."""
        import threading

        category = Category.objects.create(name='TestCat')
        product = Product.objects.create(
            category=category, name='Item', sku='ITEM-001', price=Decimal('10.00')
        )
        Inventory.objects.create(product=product, quantity=200)

        sale_a = SaleService.create_sale(cashier=cashier, items=[{'product_id': product.id, 'quantity': 1}])
        sale_b = SaleService.create_sale(cashier=cashier, items=[{'product_id': product.id, 'quantity': 1}])

        results = []
        errors = []

        def issue(sale_id, customer_doc):
            try:
                doc = BillingService.issue_document(
                    sale_id=sale_id,
                    series_code='B001',
                    document_type='boleta',
                    customer_name='Cliente',
                    customer_document_type='DNI',
                    customer_document_number=customer_doc,
                    customer_address='',
                    items=[{'description': 'Item', 'quantity': 1, 'unit_price': Decimal('10.00')}],
                )
                results.append(doc.full_number)
            except Exception as e:
                errors.append(str(e))

        t1 = threading.Thread(target=issue, args=(sale_a.id, '11111111'))
        t2 = threading.Thread(target=issue, args=(sale_b.id, '22222222'))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors, f'Unexpected errors: {errors}'
        assert len(set(results)) == 2, f'Duplicate correlativos: {results}'
