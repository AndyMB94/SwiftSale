from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from .models import BillingDocument, BillingSeries
from .ose_client import get_ose_client
from .xml_builder import build_invoice_xml

IGV_RATE = Decimal('0.18')


def _enqueue_receipt(doc_id: str):
    try:
        from .tasks import generate_and_send_receipt
        generate_and_send_receipt.delay(doc_id)
    except Exception:
        pass  # Never let task dispatch failure break the request


class BillingService:

    @staticmethod
    @transaction.atomic
    def issue_document(
        sale_id,
        series_code: str,
        document_type: str,
        customer_name: str,
        customer_document_type: str,
        customer_document_number: str,
        customer_address: str,
        items: list[dict],
        discount: Decimal = Decimal('0'),
    ) -> BillingDocument:
        from apps.sales.models import Sale

        # Validate sale exists and is completed
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            raise HttpError(404, 'Sale not found')

        if sale.status != Sale.Status.COMPLETED:
            raise HttpError(400, 'Sale must be completed before issuing a billing document')

        if BillingDocument.objects.filter(sale_id=sale_id).exists():
            raise HttpError(409, 'A billing document already exists for this sale')

        # Claim next correlativo with SELECT FOR UPDATE to prevent duplicates
        try:
            billing_series = BillingSeries.objects.select_for_update().get(
                series=series_code, document_type=document_type
            )
        except BillingSeries.DoesNotExist:
            raise HttpError(404, f'Billing series {series_code} not found for type {document_type}')

        billing_series.last_correlativo += 1
        billing_series.save(update_fields=['last_correlativo', 'updated_at'])
        correlativo = billing_series.last_correlativo
        full_number = f'{series_code}-{correlativo:08d}'

        # Calculate totals from items
        subtotal = sum(
            Decimal(str(item['unit_price'])) * item['quantity']
            for item in items
        ).quantize(Decimal('0.01'))
        tax = (subtotal * IGV_RATE).quantize(Decimal('0.01'))
        total = (subtotal - discount + tax).quantize(Decimal('0.01'))

        # Enrich items with subtotal and tax per line
        enriched_items = []
        for item in items:
            line_subtotal = (Decimal(str(item['unit_price'])) * item['quantity']).quantize(Decimal('0.01'))
            line_tax = (line_subtotal * IGV_RATE).quantize(Decimal('0.01'))
            enriched_items.append({
                'description': item['description'],
                'quantity': item['quantity'],
                'unit_price': Decimal(str(item['unit_price'])),
                'subtotal': line_subtotal,
                'tax': line_tax,
            })

        issue_date = timezone.now().date().isoformat()

        xml_content = build_invoice_xml(
            full_number=full_number,
            document_type=document_type,
            issue_date=issue_date,
            company_ruc=getattr(settings, 'COMPANY_RUC', '00000000000'),
            company_name=getattr(settings, 'COMPANY_NAME', 'SwiftSale SAC'),
            company_address=getattr(settings, 'COMPANY_ADDRESS', 'Lima, Peru'),
            customer_name=customer_name,
            customer_document_type=customer_document_type,
            customer_document_number=customer_document_number,
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            total=total,
            items=enriched_items,
        )

        doc = BillingDocument.objects.create(
            series=billing_series,
            correlativo=correlativo,
            full_number=full_number,
            document_type=document_type,
            sale=sale,
            customer_name=customer_name,
            customer_document_type=customer_document_type,
            customer_document_number=customer_document_number,
            customer_address=customer_address,
            subtotal=subtotal,
            tax=tax,
            total=total,
            xml_content=xml_content,
            status=BillingDocument.Status.PENDING,
        )

        # Send to OSE
        ose = get_ose_client()
        try:
            response = ose.send_document(
                ruc=getattr(settings, 'COMPANY_RUC', '00000000000'),
                full_number=full_number,
                xml_content=xml_content,
            )
            doc.sunat_cdr = response.cdr_content
            doc.sunat_response_code = response.response_code
            doc.status = (
                BillingDocument.Status.ACCEPTED
                if response.accepted
                else BillingDocument.Status.REJECTED
            )
            doc.save(update_fields=['sunat_cdr', 'sunat_response_code', 'status'])
        except Exception:
            doc.status = BillingDocument.Status.SENT
            doc.save(update_fields=['status'])

        # Trigger PDF generation + email after the transaction commits
        transaction.on_commit(
            lambda: _enqueue_receipt(str(doc.id))
        )

        return doc

    @staticmethod
    @transaction.atomic
    def void_document(document_id, reason: str) -> BillingDocument:
        try:
            doc = BillingDocument.objects.select_for_update().get(id=document_id)
        except BillingDocument.DoesNotExist:
            raise HttpError(404, 'Billing document not found')

        if doc.status == BillingDocument.Status.VOIDED:
            raise HttpError(409, 'Document is already voided')

        if doc.status not in (
            BillingDocument.Status.ACCEPTED,
            BillingDocument.Status.PENDING,
        ):
            raise HttpError(400, f'Cannot void a document with status {doc.status}')

        doc.status = BillingDocument.Status.VOIDED
        doc.voided_at = timezone.now()
        doc.save(update_fields=['status', 'voided_at'])

        from apps.audit.models import AuditLog
        from apps.audit.services import log_action
        log_action(
            action=AuditLog.Action.DOCUMENT_VOIDED,
            target_type='billing_document',
            target_id=str(document_id),
            metadata={'full_number': doc.full_number, 'reason': reason, 'total': str(doc.total)},
        )

        return doc
