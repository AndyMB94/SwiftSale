import api from "./api";
import type { Payment, PaymentCreateInput, PaymentListResponse } from "@/types/sales";

export const createPayment = (data: PaymentCreateInput) =>
  api.post<Payment>("/api/v1/payments", data);

export const getPayments = (params?: {
  method?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}) => api.get<PaymentListResponse>("/api/v1/payments", { params });
