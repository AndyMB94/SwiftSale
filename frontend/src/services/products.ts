import api from "./api";
import type {
  Category,
  CategoryCreateInput,
  CategoryListResponse,
  CategoryUpdateInput,
  InventoryAdjustInput,
  InventoryItem,
  InventoryMovement,
  Product,
  ProductCreateInput,
  ProductListResponse,
  ProductUpdateInput,
} from "@/types/products";

// ── Categories ────────────────────────────────────────────────────────────────

export const getCategories = (includeInactive = false) =>
  api.get<CategoryListResponse>("/api/v1/products/categories", {
    params: { include_inactive: includeInactive },
  });

export const createCategory = (data: CategoryCreateInput) =>
  api.post<Category>("/api/v1/products/categories", data);

export const updateCategory = (id: string, data: CategoryUpdateInput) =>
  api.patch<Category>(`/api/v1/products/categories/${id}`, data);

// ── Products ──────────────────────────────────────────────────────────────────

export const getProducts = (params?: {
  include_inactive?: boolean;
  category_id?: string;
}) => api.get<ProductListResponse>("/api/v1/products/products", { params });

export const createProduct = (data: ProductCreateInput) =>
  api.post<Product>("/api/v1/products/products", data);

export const updateProduct = (id: string, data: ProductUpdateInput) =>
  api.patch<Product>(`/api/v1/products/products/${id}`, data);

export const deleteProduct = (id: string) =>
  api.delete(`/api/v1/products/products/${id}`);

// ── Inventory ─────────────────────────────────────────────────────────────────

export const getInventory = (lowStockOnly = false) =>
  api.get<InventoryItem[]>("/api/v1/products/inventory", {
    params: { low_stock_only: lowStockOnly },
  });

export const adjustStock = (productId: string, data: InventoryAdjustInput) =>
  api.post<InventoryItem>(
    `/api/v1/products/inventory/${productId}/adjust`,
    data,
  );

export const getMovements = (productId: string) =>
  api.get<InventoryMovement[]>(
    `/api/v1/products/inventory/${productId}/movements`,
  );
