import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    queue="receipts",
)
def generate_and_send_receipt(self, billing_document_id: str):
    """Generate PDF receipt and email it to the customer."""
    from .models import BillingDocument
    from .pdf_builder import build_receipt_pdf

    try:
        doc = BillingDocument.objects.select_related("sale", "series").get(
            id=billing_document_id
        )
    except BillingDocument.DoesNotExist:
        logger.error(
            "BillingDocument %s not found — skipping receipt", billing_document_id
        )
        return

    items = []
    for item in doc.sale.items.select_related("product").all():
        items.append(
            {
                "description": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
        )

    try:
        pdf_bytes = build_receipt_pdf(
            full_number=doc.full_number,
            document_type=doc.document_type,
            issue_date=doc.issued_at.date().isoformat(),
            company_name=getattr(settings, "COMPANY_NAME", "SwiftSale SAC"),
            company_ruc=getattr(settings, "COMPANY_RUC", "20000000001"),
            company_address=getattr(settings, "COMPANY_ADDRESS", "Lima, Peru"),
            customer_name=doc.customer_name,
            customer_document_type=doc.customer_document_type,
            customer_document_number=doc.customer_document_number,
            items=items,
            subtotal=doc.subtotal,
            tax=doc.tax,
            discount=doc.sale.discount,
            total=doc.total,
        )
    except Exception as exc:
        logger.exception("PDF generation failed for %s", billing_document_id)
        raise self.retry(exc=exc)

    customer_email = getattr(doc.sale, "customer_email", None)
    if not customer_email:
        logger.info(
            "No customer email for document %s — skipping email", doc.full_number
        )
        _push_receipt_ready(doc)
        return

    try:
        email = EmailMessage(
            subject=f"Tu comprobante {doc.full_number} — {getattr(settings, 'COMPANY_NAME', 'SwiftSale')}",
            body=(
                f"Hola {doc.customer_name},\n\n"
                f"Adjuntamos tu comprobante electrónico {doc.full_number}.\n\n"
                f"Total pagado: S/ {doc.total}\n\n"
                f"Gracias por tu compra."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
        )
        email.attach(f"{doc.full_number}.pdf", pdf_bytes, "application/pdf")
        email.send()
        logger.info("Receipt email sent for %s", doc.full_number)
    except Exception as exc:
        logger.exception("Email delivery failed for %s", billing_document_id)
        raise self.retry(exc=exc)

    _push_receipt_ready(doc)


def _push_receipt_ready(doc):
    """Push a WebSocket notification to the cashier who made the sale."""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    cashier_id = str(doc.sale.cashier_id)
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f"user_{cashier_id}",
        {
            "type": "notification.message",
            "payload": {
                "event": "receipt.ready",
                "document_id": str(doc.id),
                "full_number": doc.full_number,
            },
        },
    )
