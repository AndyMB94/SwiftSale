import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
    queue='notifications',
)
def notify_low_stock(self, product_id: int, current_quantity: int):
    """Send email alert and push WebSocket notification for low stock."""
    from apps.products.models import Product

    try:
        product = Product.objects.select_related('category').get(id=product_id)
    except Product.DoesNotExist:
        logger.error('Product %s not found for low stock notification', product_id)
        return

    # Email alert to admin/supervisors
    try:
        recipient = getattr(settings, 'LOW_STOCK_ALERT_EMAIL', '')
        if recipient:
            send_mail(
                subject=f'[SwiftSale] Stock bajo: {product.name}',
                message=(
                    f'El producto "{product.name}" (SKU: {product.sku}) '
                    f'tiene stock bajo.\n\n'
                    f'Stock actual: {current_quantity}\n'
                    f'Umbral: {product.inventory.low_stock_threshold}\n\n'
                    f'Por favor realiza una orden de reposición.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
    except Exception as exc:
        logger.exception('Low stock email failed for product %s', product_id)
        raise self.retry(exc=exc)

    # WebSocket broadcast to all supervisors/admins would require
    # querying those users — push to a shared "admin" group instead
    _push_low_stock(product, current_quantity)


def _push_low_stock(product, current_quantity: int):
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        'staff_notifications',
        {
            'type': 'notification.message',
            'payload': {
                'event': 'inventory.low_stock',
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'current_quantity': current_quantity,
                'threshold': product.inventory.low_stock_threshold,
            },
        },
    )
