from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from ninja import Schema


class BillingItemIn(Schema):
    product_id: UUID
    quantity: int
    unit_price: Decimal
    description: str


class IssueBoletaIn(Schema):
    sale_id: UUID
    series: str
    customer_name: str
    customer_document_type: Literal['DNI', 'CE', 'PASAPORTE']
    customer_document_number: str
    items: list[BillingItemIn]


class IssueFacturaIn(Schema):
    sale_id: UUID
    series: str
    customer_name: str
    customer_document_number: str  # RUC required for factura
    customer_address: str
    items: list[BillingItemIn]


class BillingDocumentOut(Schema):
    id: UUID
    full_number: str
    document_type: str
    status: str
    customer_name: str
    customer_document_type: str
    customer_document_number: str
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    sunat_response_code: str
    issued_at: datetime
    voided_at: datetime | None


class VoidDocumentIn(Schema):
    reason: str
