export type BillingDocumentType = "boleta" | "factura";
export type BillingStatus =
  | "pending"
  | "sent"
  | "accepted"
  | "rejected"
  | "voided";
export type CustomerDocumentType = "DNI" | "CE" | "PASAPORTE";

export interface BillingSeries {
  id: number;
  series: string;
  document_type: BillingDocumentType;
  last_correlativo: number;
}

export interface BillingDocument {
  id: string;
  sale_id: string;
  full_number: string;
  document_type: BillingDocumentType;
  status: BillingStatus;
  customer_name: string;
  customer_document_type: string;
  customer_document_number: string;
  subtotal: string;
  tax: string;
  total: string;
  sunat_response_code: string;
  issued_at: string;
  voided_at: string | null;
}

export interface BillingDocumentListResponse {
  count: number;
  total_pages: number;
  page: number;
  page_size: number;
  results: BillingDocument[];
}

export interface IssueBoleta {
  sale_id: string;
  series: string;
  customer_name: string;
  customer_document_type: CustomerDocumentType;
  customer_document_number: string;
  items: BillingItem[];
}

export interface IssueFactura {
  sale_id: string;
  series: string;
  customer_name: string;
  customer_document_number: string;
  customer_address: string;
  items: BillingItem[];
}

export interface BillingItem {
  product_id: string;
  quantity: number;
  unit_price: string;
  description: string;
}
