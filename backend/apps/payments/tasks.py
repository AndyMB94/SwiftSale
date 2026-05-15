import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
    queue='notifications',
)
def notify_payment_result(self, payment_id: str):
    """Push payment.confirmed or payment.failed event to the cashier via WebSocket."""
    from .models import Payment

    try:
        payment = Payment.objects.select_related('sale__cashier').get(id=payment_id)
    except Payment.DoesNotExist:
        logger.error('Payment %s not found', payment_id)
        return

    event = (
        'payment.confirmed'
        if payment.status == Payment.Status.PAID
        else 'payment.failed'
    )

    cashier_id = str(payment.sale.cashier_id)
    _push(
        group=f'user_{cashier_id}',
        payload={
            'event': event,
            'payment_id': str(payment.id),
            'sale_id': str(payment.sale_id),
            'amount': str(payment.amount),
            'method': payment.method,
        },
    )


@shared_task(queue='maintenance')
def reconcile_stale_payments_task():
    """Periodic task — mark payments stuck in PENDING for >30 min as FAILED."""
    from .services import PaymentService

    count = PaymentService.reconcile_stale_payments()
    if count:
        logger.info('Reconciled %d stale payments', count)
    return count


def _push(group: str, payload: dict):
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        group,
        {'type': 'notification.message', 'payload': payload},
    )
