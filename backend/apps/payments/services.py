import hashlib
import hmac
import uuid
import logging
from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from ninja.errors import HttpError

from apps.sales.models import Sale
from .models import Payment

logger = logging.getLogger(__name__)

WEBHOOK_PROVIDERS = ('yape', 'plin', 'card')
STALE_PAYMENT_MINUTES = 30


def _enqueue_payment_notification(payment_id: str):
    try:
        from .tasks import notify_payment_result
        notify_payment_result.delay(payment_id)
    except Exception:
        pass


class PaymentService:

    @staticmethod
    @transaction.atomic
    def process_payment(
        sale_id: uuid.UUID,
        method: str,
        amount: Decimal,
        idempotency_key: str,
        created_by,
    ) -> tuple[Payment, bool]:
        """
        Returns (payment, created). If idempotency_key already exists,
        returns the existing payment without reprocessing.
        """
        existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False

        if method not in Payment.Method.values:
            raise HttpError(400, f"Invalid payment method '{method}'")

        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            raise HttpError(404, 'Sale not found')

        if sale.status != Sale.Status.COMPLETED:
            raise HttpError(422, 'Payment can only be processed for completed sales')

        if Payment.objects.filter(sale=sale, status=Payment.Status.PAID).exists():
            raise HttpError(409, 'Sale already has a paid payment')

        if amount != sale.total:
            raise HttpError(
                422,
                f'Amount mismatch: expected {sale.total}, received {amount}',
            )

        # Cash is confirmed immediately; others wait for webhook
        if method == Payment.Method.CASH:
            status = Payment.Status.PAID
        else:
            status = Payment.Status.PENDING

        payment = Payment.objects.create(
            sale=sale,
            method=method,
            amount=amount,
            status=status,
            idempotency_key=idempotency_key,
        )

        logger.info('payment_created', extra={
            'payment_id': str(payment.id),
            'sale_id': str(sale_id),
            'method': method,
            'status': status,
            'user_id': str(created_by.id),
        })

        return payment, True

    @staticmethod
    @transaction.atomic
    def handle_webhook(provider: str, external_id: str, provider_ref: str, status: str) -> Payment:
        """
        Processes a payment confirmation webhook from a provider.
        Idempotent: duplicate provider_ref is silently ignored.
        """
        if provider not in WEBHOOK_PROVIDERS:
            raise HttpError(400, f"Unknown provider '{provider}'")

        # Duplicate webhook detection via provider_ref
        if Payment.objects.filter(provider_ref=provider_ref).exists():
            logger.info('webhook_duplicate_ignored', extra={
                'provider': provider,
                'provider_ref': provider_ref,
            })
            return Payment.objects.get(provider_ref=provider_ref)

        try:
            payment = Payment.objects.select_for_update().get(
                idempotency_key=external_id,
                status=Payment.Status.PENDING,
            )
        except Payment.DoesNotExist:
            raise HttpError(404, 'Pending payment not found for this external_id')

        if status == 'paid':
            payment.status = Payment.Status.PAID
        elif status == 'failed':
            payment.status = Payment.Status.FAILED
        else:
            raise HttpError(400, f"Invalid status '{status}'")

        payment.provider_ref = provider_ref
        payment.save(update_fields=['status', 'provider_ref', 'updated_at'])

        logger.info('webhook_processed', extra={
            'provider': provider,
            'provider_ref': provider_ref,
            'payment_id': str(payment.id),
            'new_status': payment.status,
        })

        payment_id = str(payment.id)
        transaction.on_commit(lambda: _enqueue_payment_notification(payment_id))

        return payment

    @staticmethod
    def validate_webhook_signature(payload: bytes, signature_header: str) -> bool:
        """
        Validates HMAC-SHA256 signature from webhook provider.
        Expected header format: 'sha256=<hex_digest>'
        """
        secret = getattr(settings, 'WEBHOOK_SECRET_KEY', '')
        if not secret:
            return False
        mac = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256)
        expected = 'sha256=' + mac.hexdigest()
        return hmac.compare_digest(expected, signature_header)

    @staticmethod
    def get_payment(payment_id: uuid.UUID) -> Payment:
        try:
            return Payment.objects.select_related('sale').get(id=payment_id)
        except Payment.DoesNotExist:
            raise HttpError(404, 'Payment not found')

    @staticmethod
    def reconcile_stale_payments() -> int:
        """
        Marks payments that have been pending longer than STALE_PAYMENT_MINUTES as failed.
        In production this runs as a periodic Celery task.
        """
        cutoff = timezone.now() - timedelta(minutes=STALE_PAYMENT_MINUTES)
        stale = Payment.objects.filter(
            status=Payment.Status.PENDING,
            created_at__lt=cutoff,
        )
        count = stale.count()
        stale.update(status=Payment.Status.FAILED)

        if count:
            logger.info('payments_reconciled', extra={'marked_as_failed': count})

        return count
