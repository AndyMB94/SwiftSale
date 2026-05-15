import uuid

from django.http import HttpRequest
from ninja import Router

from apps.authentication.security import cookie_auth
from core.permissions import require_admin, require_admin_or_supervisor

from .schemas import PaymentCreateInput, PaymentOut, ReconcileOut, WebhookPayload
from .services import PaymentService

router = Router(tags=['Payments'])


@router.post('', response={201: PaymentOut}, auth=cookie_auth)
def process_payment(request: HttpRequest, payload: PaymentCreateInput):
    payment, _ = PaymentService.process_payment(
        sale_id=payload.sale_id,
        method=payload.method,
        amount=payload.amount,
        idempotency_key=payload.idempotency_key,
        created_by=request.auth,
    )
    return 201, payment


@router.get('/{payment_id}', response=PaymentOut, auth=cookie_auth)
def get_payment(request: HttpRequest, payment_id: uuid.UUID):
    require_admin_or_supervisor(request)
    return PaymentService.get_payment(payment_id)


@router.post('/webhooks/{provider}', response=PaymentOut, auth=None)
def webhook(request: HttpRequest, provider: str, payload: WebhookPayload):
    signature = request.headers.get('X-Webhook-Signature', '')
    if not PaymentService.validate_webhook_signature(request.body, signature):
        from ninja.errors import HttpError
        raise HttpError(401, 'Invalid webhook signature')

    payment = PaymentService.handle_webhook(
        provider=provider,
        external_id=payload.external_id,
        provider_ref=payload.provider_ref,
        status=payload.status,
    )
    return payment


@router.post('/reconcile', response=ReconcileOut, auth=cookie_auth)
def reconcile(request: HttpRequest):
    require_admin(request)
    count = PaymentService.reconcile_stale_payments()
    return ReconcileOut(marked_as_failed=count)
