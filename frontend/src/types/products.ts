export interface Category {
  id: number;
  name: string;
  description: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  sku: string;
  barcode: string | null;
  price: string;
  category: Category;
  is_active: boolean;
  created_at: string;
}

export interface ProductCreateInput {
  name: string;
  description?: string;
  sku: string;
  barcode?: string;
  price: string;
  category_id: number;
}

export interface ProductUpdateInput extends Partial<ProductCreateInput> {}

export interface InventoryItem {
  id: number;
  product: Product;
  quantity: number;
  min_quantity: number;
  is_low_stock: boolean;
}

export interface StockMovement {
  id: number;
  product: number;
  quantity_change: number;
  movement_type: "sale" | "purchase" | "adjustment" | "return";
  reason: string;
  created_at: string;
  created_by: string;
}

export type AdjustmentReason =
  | "damaged_goods"
  | "purchase"
  | "return"
  | "correction";
