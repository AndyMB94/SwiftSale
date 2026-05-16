"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, Search, Tag, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  createCategory,
  createProduct,
  deleteProduct,
  getCategories,
  getProducts,
  updateCategory,
  updateProduct,
} from "@/services/products";
import { formatCurrency } from "@/utils/formatters";
import type {
  Category,
  Product,
  ProductCreateInput,
} from "@/types/products";

// ── Product form state ────────────────────────────────────────────────────────

const EMPTY_FORM = {
  name: "",
  sku: "",
  barcode: "",
  price: "",
  description: "",
  category_id: "",
};

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ProductsPage() {
  const qc = useQueryClient();

  // Filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [includeInactive, setIncludeInactive] = useState(false);

  // Product sheet
  const [productSheet, setProductSheet] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  // Delete dialog
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);

  // Category sheet
  const [catSheet, setCatSheet] = useState(false);
  const [newCatName, setNewCatName] = useState("");
  const [newCatDesc, setNewCatDesc] = useState("");

  // ── Queries ────────────────────────────────────────────────────────────────

  const { data: productsRes, isLoading: loadingProducts } = useQuery({
    queryKey: ["products", { includeInactive, categoryFilter }],
    queryFn: () =>
      getProducts({
        include_inactive: includeInactive,
        category_id: categoryFilter !== "all" ? categoryFilter : undefined,
      }),
  });

  const { data: categoriesRes } = useQuery({
    queryKey: ["categories"],
    queryFn: () => getCategories(true),
  });

  const products = productsRes?.data.results ?? [];
  const categories = categoriesRes?.data.results ?? [];

  const filtered = useMemo(() => {
    if (!search.trim()) return products;
    const q = search.toLowerCase();
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.sku.toLowerCase().includes(q) ||
        p.barcode?.toLowerCase().includes(q),
    );
  }, [products, search]);

  // ── Mutations ──────────────────────────────────────────────────────────────

  const createMutation = useMutation({
    mutationFn: (data: ProductCreateInput) => createProduct(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      toast.success("Producto creado correctamente");
      closeProductSheet();
    },
    onError: () => toast.error("Error al crear el producto"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ProductCreateInput> }) =>
      updateProduct(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      toast.success("Producto actualizado");
      closeProductSheet();
    },
    onError: () => toast.error("Error al actualizar el producto"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProduct(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      toast.success("Producto eliminado");
      setDeleteTarget(null);
    },
    onError: () => toast.error("Error al eliminar el producto"),
  });

  const createCatMutation = useMutation({
    mutationFn: () => createCategory({ name: newCatName, description: newCatDesc }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["categories"] });
      toast.success("Categoría creada");
      setNewCatName("");
      setNewCatDesc("");
    },
    onError: () => toast.error("Error al crear la categoría"),
  });

  const toggleCatMutation = useMutation({
    mutationFn: (cat: Category) =>
      updateCategory(cat.id, { is_active: !cat.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
    onError: () => toast.error("Error al actualizar la categoría"),
  });

  // ── Helpers ────────────────────────────────────────────────────────────────

  function openCreate() {
    setEditingProduct(null);
    setForm(EMPTY_FORM);
    setProductSheet(true);
  }

  function openEdit(p: Product) {
    setEditingProduct(p);
    setForm({
      name: p.name,
      sku: p.sku,
      barcode: p.barcode ?? "",
      price: p.price,
      description: p.description,
      category_id: p.category_id,
    });
    setProductSheet(true);
  }

  function closeProductSheet() {
    setProductSheet(false);
    setEditingProduct(null);
    setForm(EMPTY_FORM);
  }

  function handleSave() {
    if (!form.name || !form.sku || !form.price || !form.category_id) {
      toast.error("Completa todos los campos obligatorios");
      return;
    }
    const payload: ProductCreateInput = {
      name: form.name,
      sku: form.sku,
      price: form.price,
      category_id: form.category_id,
      description: form.description || undefined,
      barcode: form.barcode || undefined,
    };
    if (editingProduct) {
      updateMutation.mutate({ id: editingProduct.id, data: payload });
    } else {
      createMutation.mutate(payload);
    }
  }

  const saving = createMutation.isPending || updateMutation.isPending;

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Productos</h2>
          <p className="text-sm text-slate-500">
            {loadingProducts ? "Cargando..." : `${filtered.length} producto${filtered.length !== 1 ? "s" : ""}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setCatSheet(true)}>
            <Tag size={14} className="mr-1.5" />
            Categorías
          </Button>
          <Button size="sm" onClick={openCreate}>
            <Plus size={14} className="mr-1.5" />
            Nuevo producto
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="Buscar por nombre, SKU o código..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-9"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-48 h-9">
            <SelectValue placeholder="Todas las categorías" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las categorías</SelectItem>
            {categories.filter((c) => c.is_active).map((cat) => (
              <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant={includeInactive ? "secondary" : "ghost"}
          size="sm"
          onClick={() => setIncludeInactive((v) => !v)}
          className="h-9 text-xs"
        >
          {includeInactive ? "Ocultar inactivos" : "Mostrar inactivos"}
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead>Categoría</TableHead>
              <TableHead className="text-right">Precio</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-20" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {loadingProducts ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-400 py-10 text-sm">
                  {search ? "Sin resultados para la búsqueda" : "No hay productos registrados"}
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((product) => (
                <TableRow key={product.id} className={!product.is_active ? "opacity-50" : ""}>
                  <TableCell className="font-medium">{product.name}</TableCell>
                  <TableCell className="text-slate-500 font-mono text-xs">{product.sku}</TableCell>
                  <TableCell className="text-slate-500">{product.category_name}</TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(product.price)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={product.is_active ? "default" : "secondary"}>
                      {product.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 justify-end">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => openEdit(product)}
                      >
                        <Pencil size={13} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 hover:text-destructive"
                        onClick={() => setDeleteTarget(product)}
                      >
                        <Trash2 size={13} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Product Sheet */}
      <Sheet open={productSheet} onOpenChange={(o) => { if (!o) closeProductSheet(); }}>
        <SheetContent className="w-[420px] sm:w-[480px] overflow-y-auto" aria-describedby={undefined}>
          <SheetHeader>
            <SheetTitle>{editingProduct ? "Editar producto" : "Nuevo producto"}</SheetTitle>
          </SheetHeader>
          <div className="space-y-4 px-4 pb-6">
            <div className="space-y-1.5">
              <Label>Categoría *</Label>
              <Select value={form.category_id} onValueChange={(v) => setForm((f) => ({ ...f, category_id: v }))}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleccionar categoría" />
                </SelectTrigger>
                <SelectContent>
                  {categories.filter((c) => c.is_active).map((cat) => (
                    <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Nombre *</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Nombre del producto"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Descripción</Label>
              <textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Descripción opcional"
                rows={2}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>SKU *</Label>
                <Input
                  value={form.sku}
                  onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))}
                  placeholder="SKU-001"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Código de barras</Label>
                <Input
                  value={form.barcode}
                  onChange={(e) => setForm((f) => ({ ...f, barcode: e.target.value }))}
                  placeholder="Opcional"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Precio (S/) *</Label>
              <Input
                type="number"
                min="0"
                step="0.01"
                value={form.price}
                onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
                placeholder="0.00"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button className="flex-1" onClick={handleSave} disabled={saving}>
                {saving ? "Guardando..." : editingProduct ? "Actualizar" : "Crear producto"}
              </Button>
              <Button variant="outline" onClick={closeProductSheet}>Cancelar</Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* Delete Dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(o) => { if (!o) setDeleteTarget(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Eliminar producto?</DialogTitle>
            <DialogDescription>
              <strong>{deleteTarget?.name}</strong> será desactivado y no aparecerá en el POS.
              Puedes reactivarlo en cualquier momento.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
            >
              {deleteMutation.isPending ? "Eliminando..." : "Eliminar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Category Sheet */}
      <Sheet open={catSheet} onOpenChange={setCatSheet}>
        <SheetContent className="w-[380px] overflow-y-auto" aria-describedby={undefined}>
          <SheetHeader>
            <SheetTitle>Gestionar categorías</SheetTitle>
          </SheetHeader>
          <div className="space-y-5 mt-6">
            {/* New category form */}
            <div className="space-y-3 p-4 rounded-lg border border-border bg-muted/40">
              <p className="text-sm font-medium">Nueva categoría</p>
              <Input
                placeholder="Nombre"
                value={newCatName}
                onChange={(e) => setNewCatName(e.target.value)}
              />
              <Input
                placeholder="Descripción (opcional)"
                value={newCatDesc}
                onChange={(e) => setNewCatDesc(e.target.value)}
              />
              <Button
                size="sm"
                className="w-full"
                disabled={!newCatName.trim() || createCatMutation.isPending}
                onClick={() => createCatMutation.mutate()}
              >
                {createCatMutation.isPending ? "Creando..." : "Crear categoría"}
              </Button>
            </div>
            {/* Category list */}
            <div className="space-y-2">
              {categories.map((cat) => (
                <div
                  key={cat.id}
                  className="flex items-center justify-between py-2 px-3 rounded-md border border-border bg-card"
                >
                  <div>
                    <p className="text-sm font-medium">{cat.name}</p>
                    {cat.description && (
                      <p className="text-xs text-slate-400">{cat.description}</p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={`text-xs h-7 ${cat.is_active ? "text-slate-500" : "text-primary"}`}
                    onClick={() => toggleCatMutation.mutate(cat)}
                  >
                    {cat.is_active ? "Desactivar" : "Activar"}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
