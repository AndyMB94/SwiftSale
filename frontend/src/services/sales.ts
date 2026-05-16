import api from "./api";
import type { Sale, SaleCreateInput } from "@/types/sales";

export const createSale = (data: SaleCreateInput) =>
  api.post<Sale>("/api/v1/sales", data);
