import uuid
from datetime import date

from django.http import HttpRequest
from ninja import Router

from apps.authentication.security import cookie_auth
from core.permissions import require_admin_or_supervisor

from .schemas import SaleCreateInput, SaleListOut, SaleOut
from .services import SaleService

router = Router(tags=["Sales"])


@router.post("", response={201: SaleOut}, auth=cookie_auth)
def create_sale(request: HttpRequest, payload: SaleCreateInput):
    items = [
        {"product_id": i.product_id, "quantity": i.quantity} for i in payload.items
    ]
    sale = SaleService.create_sale(
        cashier=request.auth,
        items=items,
        discount=payload.discount,
    )
    return 201, SaleOut.from_orm(sale)


@router.get("", response=SaleListOut, auth=cookie_auth)
def list_sales(
    request: HttpRequest,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
):
    require_admin_or_supervisor(request)
    sales, count, total_pages = SaleService.list_sales(
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    from .schemas import SaleListItemOut

    return SaleListOut(
        count=count,
        total_pages=total_pages,
        page=page,
        page_size=page_size,
        results=[SaleListItemOut.from_orm(s) for s in sales],
    )


@router.get("/{sale_id}", response=SaleOut, auth=cookie_auth)
def get_sale(request: HttpRequest, sale_id: uuid.UUID):
    require_admin_or_supervisor(request)
    return SaleOut.from_orm(SaleService.get_sale(sale_id))


@router.post("/{sale_id}/cancel", response=SaleOut, auth=cookie_auth)
def cancel_sale(request: HttpRequest, sale_id: uuid.UUID):
    require_admin_or_supervisor(request)
    sale = SaleService.cancel_sale(sale_id, cancelled_by=request.auth)
    return SaleOut.from_orm(SaleService.get_sale(sale.id))
