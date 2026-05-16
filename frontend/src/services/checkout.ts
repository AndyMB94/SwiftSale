import api from "./api";
import type { CheckoutInput, CheckoutOut } from "@/types/sales";

export const createCheckout = (data: CheckoutInput) =>
  api.post<CheckoutOut>("/api/v1/checkout", data);
