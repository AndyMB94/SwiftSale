import { create } from "zustand";
import type { CartItem, PaymentMethod } from "@/types/sales";
import type { Product } from "@/types/products";

interface PosState {
  items: CartItem[];
  discount: string;
  paymentMethod: PaymentMethod | null;
  addItem: (product: Product) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, qty: number) => void;
  setDiscount: (discount: string) => void;
  setPaymentMethod: (method: PaymentMethod) => void;
  clearCart: () => void;
}

export const usePosStore = create<PosState>((set) => ({
  items: [],
  discount: "0.00",
  paymentMethod: null,

  addItem: (product) =>
    set((state) => {
      const existing = state.items.find((i) => i.product.id === product.id);
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.product.id === product.id
              ? { ...i, quantity: i.quantity + 1 }
              : i,
          ),
        };
      }
      return {
        items: [
          ...state.items,
          { product, quantity: 1, unit_price: product.price },
        ],
      };
    }),

  removeItem: (productId) =>
    set((state) => ({
      items: state.items.filter((i) => i.product.id !== productId),
    })),

  updateQuantity: (productId, qty) =>
    set((state) => ({
      items:
        qty <= 0
          ? state.items.filter((i) => i.product.id !== productId)
          : state.items.map((i) =>
              i.product.id === productId ? { ...i, quantity: qty } : i,
            ),
    })),

  setDiscount: (discount) => set({ discount }),

  setPaymentMethod: (method) => set({ paymentMethod: method }),

  clearCart: () =>
    set({ items: [], discount: "0.00", paymentMethod: null }),
}));
