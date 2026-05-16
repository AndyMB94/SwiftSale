import api from "./api";
import type { Payment, PaymentCreateInput } from "@/types/sales";

export const createPayment = (data: PaymentCreateInput) =>
  api.post<Payment>("/api/v1/payments", data);
