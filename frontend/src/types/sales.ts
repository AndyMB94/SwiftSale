import type { Product } from "./products";

export type PaymentMethod = "cash" | "card" | "yape" | "plin";
export type SaleStatus = "pending" | "completed" | "cancelled";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";

export interface CartItem {
  product: Product;
  quantity: number;
  unit_price: string;
}

export interface SaleItemOut {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export interface Sale {
  id: string;
  cashier_id: string;
  cashier_name: string;
  status: SaleStatus;
  subtotal: string;
  discount: string;
  tax: string;
  total: string;
  items: SaleItemOut[];
  created_at: string;
}

export interface SaleCreateInput {
  items: { product_id: string; quantity: number }[];
  discount?: string;
}

export interface Payment {
  id: string;
  sale_id: string;
  method: PaymentMethod;
  amount: string;
  status: PaymentStatus;
  provider_ref: string | null;
  idempotency_key: string;
  created_at: string;
}

export interface PaymentCreateInput {
  sale_id: string;
  method: PaymentMethod;
  amount: string;
  idempotency_key: string;
}
