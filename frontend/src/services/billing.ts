import api from "./api";
import type {
  BillingDocument,
  BillingDocumentListResponse,
  BillingSeries,
  IssueBoleta,
  IssueFactura,
} from "@/types/billing";

export const getBillingSeries = () =>
  api.get<BillingSeries[]>("/api/v1/billing/series");

export const getBillingDocuments = (params?: {
  document_type?: string;
  status?: string;
  sale_id?: string;
  page?: number;
  page_size?: number;
}) => api.get<BillingDocumentListResponse>("/api/v1/billing", { params });

export const issueBoleta = (data: IssueBoleta) =>
  api.post<BillingDocument>("/api/v1/billing/boleta", data);

export const issueFactura = (data: IssueFactura) =>
  api.post<BillingDocument>("/api/v1/billing/factura", data);

export const voidDocument = (documentId: string, reason: string) =>
  api.post<BillingDocument>(`/api/v1/billing/${documentId}/void`, { reason });
