export interface Category {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface CategoryListResponse {
  count: number;
  results: Category[];
}

export interface CategoryCreateInput {
  name: string;
  description?: string;
}

export interface CategoryUpdateInput {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface Product {
  id: string;
  category_id: string;
  category_name: string;
  name: string;
  description: string;
  sku: string;
  barcode: string | null;
  price: string;
  is_active: boolean;
  created_at: string;
}

export interface ProductListResponse {
  count: number;
  total_pages: number;
  page: number;
  page_size: number;
  results: Product[];
}

export interface ProductCreateInput {
  category_id: string;
  name: string;
  description?: string;
  sku: string;
  barcode?: string;
  price: string;
}

export interface ProductUpdateInput {
  category_id?: string;
  name?: string;
  description?: string;
  sku?: string;
  barcode?: string;
  price?: string;
  is_active?: boolean;
}

export interface InventoryItem {
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  low_stock_threshold: number;
  is_low_stock: boolean;
  updated_at: string;
}

export interface InventoryListResponse {
  count: number;
  total_pages: number;
  page: number;
  page_size: number;
  results: InventoryItem[];
}

export interface InventoryAdjustInput {
  quantity_delta: number;
  reason: string;
}

export type MovementType = "sale" | "purchase" | "adjustment" | "return";

export interface InventoryMovement {
  id: string;
  movement_type: MovementType;
  quantity_delta: number;
  quantity_after: number;
  reason: string;
  created_at: string;
}

export type AdjustmentReason =
  | "purchase"
  | "return"
  | "damaged_goods"
  | "correction";
