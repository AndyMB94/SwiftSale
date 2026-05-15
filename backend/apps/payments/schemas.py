import uuid
from decimal import Decimal
from datetime import datetime
from ninja import Schema


class PaymentCreateInput(Schema):
    sale_id: uuid.UUID
    method: str
    amount: Decimal
    idempotency_key: str


class PaymentOut(Schema):
    id: uuid.UUID
    sale_id: uuid.UUID
    method: str
    amount: Decimal
    status: str
    provider_ref: str | None
    idempotency_key: str
    created_at: datetime


class WebhookPayload(Schema):
    external_id: str       # our idempotency_key — links webhook to our payment
    provider_ref: str      # provider's unique transaction ID
    status: str            # 'paid' or 'failed'
    amount: Decimal


class ReconcileOut(Schema):
    marked_as_failed: int
