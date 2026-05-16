import api from "./api";
import type { Sale, SaleCreateInput, SaleListResponse } from "@/types/sales";

export const createSale = (data: SaleCreateInput) =>
  api.post<Sale>("/api/v1/sales", data);

export const getSales = (params?: {
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}) => api.get<SaleListResponse>("/api/v1/sales", { params });

export const getSale = (saleId: string) =>
  api.get<Sale>(`/api/v1/sales/${saleId}`);

export const cancelSale = (saleId: string) =>
  api.post<Sale>(`/api/v1/sales/${saleId}/cancel`);
