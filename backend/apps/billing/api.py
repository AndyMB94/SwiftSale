from uuid import UUID

from ninja import Router
from ninja.errors import HttpError

from apps.authentication.security import CookieJWTAuth

from .models import BillingDocument
from .schemas import BillingDocumentOut, IssueBoletaIn, IssueFacturaIn, VoidDocumentIn
from .services import BillingService

router = Router(tags=['billing'])
auth = CookieJWTAuth()


def _doc_to_out(doc: BillingDocument) -> BillingDocumentOut:
    return BillingDocumentOut(
        id=doc.id,
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


@router.post('/boleta', response=BillingDocumentOut, auth=auth)
def issue_boleta(request, payload: IssueBoletaIn):
    items = [
        {
            'description': it.description,
            'quantity': it.quantity,
            'unit_price': it.unit_price,
        }
        for it in payload.items
    ]
    doc = BillingService.issue_document(
        sale_id=payload.sale_id,
        series_code=payload.series,
        document_type='boleta',
        customer_name=payload.customer_name,
        customer_document_type=payload.customer_document_type,
        customer_document_number=payload.customer_document_number,
        customer_address='',
        items=items,
    )
    return _doc_to_out(doc)


@router.post('/factura', response=BillingDocumentOut, auth=auth)
def issue_factura(request, payload: IssueFacturaIn):
    items = [
        {
            'description': it.description,
            'quantity': it.quantity,
            'unit_price': it.unit_price,
        }
        for it in payload.items
    ]
    doc = BillingService.issue_document(
        sale_id=payload.sale_id,
        series_code=payload.series,
        document_type='factura',
        customer_name=payload.customer_name,
        customer_document_type='RUC',
        customer_document_number=payload.customer_document_number,
        customer_address=payload.customer_address,
        items=items,
    )
    return _doc_to_out(doc)


@router.get('', response=list[BillingDocumentOut], auth=auth)
def list_documents(request):
    docs = BillingDocument.objects.select_related('series').order_by('-issued_at')
    return [_doc_to_out(d) for d in docs]


@router.get('/{document_id}', response=BillingDocumentOut, auth=auth)
def get_document(request, document_id: UUID):
    try:
        doc = BillingDocument.objects.get(id=document_id)
    except BillingDocument.DoesNotExist:
        raise HttpError(404, 'Billing document not found')
    return _doc_to_out(doc)


@router.post('/{document_id}/void', response=BillingDocumentOut, auth=auth)
def void_document(request, document_id: UUID, payload: VoidDocumentIn):
    doc = BillingService.void_document(document_id=document_id, reason=payload.reason)
    return _doc_to_out(doc)
