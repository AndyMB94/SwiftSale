import type { Product } from "./products";

export type PaymentMethod = "cash" | "card" | "yape" | "plin";
export type SaleStatus = "pending" | "completed" | "cancelled";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";

export interface SaleItem {
  id: number;
  product: Product;
  quantity: number;
  unit_price: string;
  subtotal: string;
}

export interface Sale {
  id: number;
  items: SaleItem[];
  subtotal: string;
  igv: string;
  discount: string;
  total: string;
  payment_method: PaymentMethod;
  status: SaleStatus;
  cashier: string;
  created_at: string;
  billing_document?: number | null;
}

export interface CartItem {
  product: Product;
  quantity: number;
  unit_price: string;
}

export interface SaleCreateInput {
  items: { product_id: number; quantity: number; unit_price: string }[];
  payment_method: PaymentMethod;
  discount?: string;
  customer_amount?: string;
}

export interface Payment {
  id: number;
  sale: number;
  amount: string;
  method: PaymentMethod;
  status: PaymentStatus;
  reference_code: string | null;
  created_at: string;
}
