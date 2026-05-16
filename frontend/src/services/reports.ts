import api from "./api";
import type {
  BestSellersResponse,
  DailyRevenueResponse,
  InventoryValuationResponse,
} from "@/types/reports";

export const getRevenue = (params: { start?: string; end?: string }) =>
  api.get<DailyRevenueResponse>("/api/v1/reports/revenue", { params });

export const getBestSellers = (params: {
  start?: string;
  end?: string;
  limit?: number;
}) => api.get<BestSellersResponse>("/api/v1/reports/best-sellers", { params });

export const getInventoryValuation = () =>
  api.get<InventoryValuationResponse>("/api/v1/reports/inventory-valuation");
