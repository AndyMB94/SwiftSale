export interface DailyRevenueRow {
  date: string;
  revenue: string;
  sale_count: number;
  avg_ticket: string;
}

export interface DailyRevenueResponse {
  start: string;
  end: string;
  total_revenue: string;
  total_sales: number;
  rows: DailyRevenueRow[];
}

export interface BestSellerRow {
  product_id: number;
  product_name: string;
  sku: string;
  total_quantity: number;
  total_revenue: string;
}

export interface BestSellersResponse {
  start: string;
  end: string;
  rows: BestSellerRow[];
}

export interface InventoryValuationRow {
  product_id: number;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: string;
  valuation: string;
}

export interface InventoryValuationResponse {
  total_valuation: string;
  rows: InventoryValuationRow[];
}
