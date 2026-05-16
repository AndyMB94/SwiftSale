from decimal import Decimal

from django.db import transaction
from django.http import HttpRequest
from ninja import Router, Schema

from apps.authentication.security import cookie_auth
from apps.payments.schemas import PaymentOut
from apps.payments.services import PaymentService

from .schemas import SaleItemInput, SaleOut
from .services import SaleService

router = Router(tags=["Checkout"])


class CheckoutInput(Schema):
    items: list[SaleItemInput]
    discount: Decimal = Decimal("0")
    method: str
    idempotency_key: str


class CheckoutOut(Schema):
    sale: SaleOut
    payment: PaymentOut


class CheckoutService:
    @staticmethod
    @transaction.atomic
    def checkout(
        cashier,
        items: list[dict],
        discount: Decimal,
        method: str,
        idempotency_key: str,
    ):
        sale = SaleService.create_sale(cashier, items, discount)
        payment, _ = PaymentService.process_payment(
            sale_id=sale.id,
            method=method,
            amount=sale.total,
            idempotency_key=idempotency_key,
            created_by=cashier,
        )
        return sale, payment


@router.post("", response={201: CheckoutOut}, auth=cookie_auth)
def checkout(request: HttpRequest, payload: CheckoutInput):
    items = [
        {"product_id": i.product_id, "quantity": i.quantity} for i in payload.items
    ]
    sale, payment = CheckoutService.checkout(
        cashier=request.auth,
        items=items,
        discount=payload.discount,
        method=payload.method,
        idempotency_key=payload.idempotency_key,
    )
    return 201, CheckoutOut(sale=SaleOut.from_orm(sale), payment=payment)
