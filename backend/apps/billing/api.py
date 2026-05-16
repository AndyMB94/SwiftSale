import math
from uuid import UUID

from ninja import Router
from ninja.errors import HttpError

from apps.authentication.security import cookie_auth
from core.permissions import require_admin

from .models import BillingDocument, BillingSeries
from .schemas import (
    BillingDocumentListOut,
    BillingDocumentOut,
    BillingSeriesOut,
    IssueBoletaIn,
    IssueFacturaIn,
    VoidDocumentIn,
)
from .services import BillingService

router = Router(tags=["billing"])


def _doc_to_out(doc: BillingDocument) -> BillingDocumentOut:
    return BillingDocumentOut(
        id=doc.id,
        sale_id=doc.sale_id,
        full_number=doc.full_number,
        document_type=doc.document_type,
        status=doc.status,
        customer_name=doc.customer_name,
        customer_document_type=doc.customer_document_type,
        customer_document_number=doc.customer_document_number,
        subtotal=doc.subtotal,
        tax=doc.tax,
        total=doc.total,
        sunat_response_code=doc.sunat_response_code,
        issued_at=doc.issued_at,
        voided_at=doc.voided_at,
    )


@router.get("/series", response=list[BillingSeriesOut], auth=cookie_auth)
def list_series(request):
    return list(BillingSeries.objects.all().order_by("document_type", "series"))


@router.get("", response=BillingDocumentListOut, auth=cookie_auth)
def list_documents(
    request,
    document_type: str | None = None,
    status: str | None = None,
    sale_id: UUID | None = None,
    page: int = 1,
    page_size: int = 20,
):
    qs = BillingDocument.objects.select_related("series").order_by("-issued_at")
    if document_type:
        qs = qs.filter(document_type=document_type)
    if status:
        qs = qs.filter(status=status)
    if sale_id:
        qs = qs.filter(sale_id=sale_id)
    count = qs.count()
    total_pages = max(1, math.ceil(count / page_size))
    page = max(1, min(page, total_pages))
    offset = (page - 1) * page_size
    results = [_doc_to_out(d) for d in qs[offset : offset + page_size]]
    return BillingDocumentListOut(
        count=count,
        total_pages=total_pages,
        page=page,
        page_size=page_size,
        results=results,
    )


@router.get("/{document_id}", response=BillingDocumentOut, auth=cookie_auth)
def get_document(request, document_id: UUID):
    try:
        doc = BillingDocument.objects.get(id=document_id)
    except BillingDocument.DoesNotExist:
        raise HttpError(404, "Billing document not found")
    return _doc_to_out(doc)


@router.post("/boleta", response=BillingDocumentOut, auth=cookie_auth)
def issue_boleta(request, payload: IssueBoletaIn):
    items = [
        {
            "description": it.description,
            "quantity": it.quantity,
            "unit_price": it.unit_price,
        }
        for it in payload.items
    ]
    doc = BillingService.issue_document(
        sale_id=payload.sale_id,
        series_code=payload.series,
        document_type="boleta",
        customer_name=payload.customer_name,
        customer_document_type=payload.customer_document_type,
        customer_document_number=payload.customer_document_number,
        customer_address="",
        items=items,
    )
    return _doc_to_out(doc)


@router.post("/factura", response=BillingDocumentOut, auth=cookie_auth)
def issue_factura(request, payload: IssueFacturaIn):
    items = [
        {
            "description": it.description,
            "quantity": it.quantity,
            "unit_price": it.unit_price,
        }
        for it in payload.items
    ]
    doc = BillingService.issue_document(
        sale_id=payload.sale_id,
        series_code=payload.series,
        document_type="factura",
        customer_name=payload.customer_name,
        customer_document_type="RUC",
        customer_document_number=payload.customer_document_number,
        customer_address=payload.customer_address,
        items=items,
    )
    return _doc_to_out(doc)


@router.post("/{document_id}/void", response=BillingDocumentOut, auth=cookie_auth)
def void_document(request, document_id: UUID, payload: VoidDocumentIn):
    require_admin(request)
    doc = BillingService.void_document(document_id=document_id, reason=payload.reason)
    return _doc_to_out(doc)
