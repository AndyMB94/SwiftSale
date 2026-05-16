"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ChevronLeft, ChevronRight, History, Search } from "lucide-react";
import { usePageTitle } from "@/hooks/usePageTitle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { adjustStock, getInventory, getMovements } from "@/services/products";
import { formatDateTime } from "@/utils/formatters";
import { ADJUSTMENT_REASONS } from "@/utils/constants";
import type { InventoryItem, InventoryMovement } from "@/types/products";

const PAGE_SIZE = 20;

const MOVEMENT_LABELS: Record<string, string> = {
  sale: "Venta",
  purchase: "Compra",
  adjustment: "Ajuste",
  return: "Devolución",
};

export default function InventoryPage() {
  usePageTitle("Inventario");
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [page, setPage] = useState(1);

  // Adjust dialog
  const [adjustTarget, setAdjustTarget] = useState<InventoryItem | null>(null);
  const [delta, setDelta] = useState("");
  const [reason, setReason] = useState<string>("");

  // Movements sheet
  const [movementsTarget, setMovementsTarget] = useState<InventoryItem | null>(null);

  // Debounce search — 350 ms
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 350);
    return () => clearTimeout(t);
  }, [search]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, lowStockOnly]);

  // ── Queries ────────────────────────────────────────────────────────────────

  const { data: inventoryRes, isLoading } = useQuery({
    queryKey: ["inventory", { lowStockOnly, debouncedSearch, page }],
    queryFn: () =>
      getInventory({
        low_stock_only: lowStockOnly,
        search: debouncedSearch || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const { data: movementsRes, isLoading: loadingMovements } = useQuery({
    queryKey: ["movements", movementsTarget?.product_id],
    queryFn: () => getMovements(movementsTarget!.product_id),
    enabled: !!movementsTarget,
  });

  const inventory = inventoryRes?.data.results ?? [];
  const totalCount = inventoryRes?.data.count ?? 0;
  const totalPages = inventoryRes?.data.total_pages ?? 1;
  const movements: InventoryMovement[] = movementsRes?.data ?? [];

  const pageStart = totalCount === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const pageEnd = Math.min(page * PAGE_SIZE, totalCount);

  // ── Mutations ──────────────────────────────────────────────────────────────

  const adjustMutation = useMutation({
    mutationFn: () =>
      adjustStock(adjustTarget!.product_id, {
        quantity_delta: Number(delta),
        reason,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inventory"] });
      toast.success("Stock ajustado correctamente");
      setAdjustTarget(null);
      setDelta("");
      setReason("");
    },
    onError: () => toast.error("Error al ajustar el stock"),
  });

  function openAdjust(item: InventoryItem) {
    setAdjustTarget(item);
    setDelta("");
    setReason("");
  }

  function handleAdjust() {
    if (!delta || !reason) {
      toast.error("Completa todos los campos");
      return;
    }
    if (Number(delta) === 0) {
      toast.error("El ajuste no puede ser cero");
      return;
    }
    adjustMutation.mutate();
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight">Inventario</h2>
          <p className="text-sm text-slate-500">
            {isLoading ? "Cargando..." : `${totalCount} producto${totalCount !== 1 ? "s" : ""}`}
          </p>
        </div>
        <Button
          variant={lowStockOnly ? "secondary" : "outline"}
          size="sm"
          onClick={() => setLowStockOnly((v) => !v)}
        >
          {lowStockOnly ? "Ver todos" : "Solo stock bajo"}
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Buscar por nombre o SKU..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8 h-9"
        />
      </div>

      {/* Table */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead className="text-right">Stock actual</TableHead>
              <TableHead className="text-right">Stock mínimo</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-32" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))
            ) : inventory.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-slate-400 py-10 text-sm">
                  {debouncedSearch
                    ? "Sin resultados para la búsqueda"
                    : lowStockOnly
                    ? "No hay productos con stock bajo"
                    : "Sin registros de inventario"}
                </TableCell>
              </TableRow>
            ) : (
              inventory.map((item) => (
                <TableRow
                  key={item.product_id}
                  className={item.is_low_stock ? "bg-warning/5" : ""}
                >
                  <TableCell className="font-medium">{item.product_name}</TableCell>
                  <TableCell className="text-slate-500 font-mono text-xs">{item.sku}</TableCell>
                  <TableCell className={`text-right font-semibold ${item.is_low_stock ? "text-warning" : ""}`}>
                    {item.quantity}
                  </TableCell>
                  <TableCell className="text-right text-slate-400">
                    {item.low_stock_threshold}
                  </TableCell>
                  <TableCell>
                    {item.is_low_stock ? (
                      <Badge className="bg-warning/10 text-warning border-warning/20 hover:bg-warning/10">
                        Stock bajo
                      </Badge>
                    ) : (
                      <Badge variant="secondary">Normal</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1 justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => openAdjust(item)}
                      >
                        Ajustar
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7"
                        onClick={() => setMovementsTarget(item)}
                      >
                        <History size={13} />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination footer */}
        {!isLoading && totalCount > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-slate-500">
            <span>
              Mostrando {pageStart}–{pageEnd} de {totalCount} productos
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft size={14} />
              </Button>
              <span className="text-xs tabular-nums">
                Página {page} de {totalPages}
              </span>
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7"
                disabled={page === totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight size={14} />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Adjust Dialog */}
      <Dialog open={!!adjustTarget} onOpenChange={(o) => { if (!o) setAdjustTarget(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajustar stock — {adjustTarget?.product_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="flex items-center gap-3 p-3 rounded-md bg-muted text-sm">
              <span className="text-slate-500">Stock actual:</span>
              <span className="font-semibold">{adjustTarget?.quantity} unidades</span>
            </div>
            <div className="space-y-1.5">
              <Label>Cantidad a ajustar *</Label>
              <Input
                type="number"
                placeholder="Positivo para entrada, negativo para salida"
                value={delta}
                onChange={(e) => setDelta(e.target.value)}
              />
              <p className="text-xs text-slate-400">Ej: +10 para ingresar, -5 para descontar</p>
            </div>
            <div className="space-y-1.5">
              <Label>Motivo *</Label>
              <Select value={reason} onValueChange={setReason}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleccionar motivo" />
                </SelectTrigger>
                <SelectContent>
                  {ADJUSTMENT_REASONS.map((r) => (
                    <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAdjustTarget(null)}>Cancelar</Button>
            <Button onClick={handleAdjust} disabled={adjustMutation.isPending}>
              {adjustMutation.isPending ? "Guardando..." : "Confirmar ajuste"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Movements Sheet */}
      <Sheet open={!!movementsTarget} onOpenChange={(o) => { if (!o) setMovementsTarget(null); }}>
        <SheetContent className="w-105 overflow-y-auto" aria-describedby={undefined}>
          <SheetHeader>
            <SheetTitle>Movimientos — {movementsTarget?.product_name}</SheetTitle>
          </SheetHeader>
          <div className="mt-6">
            {loadingMovements ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 w-full" />
                ))}
              </div>
            ) : movements.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-8">Sin movimientos registrados</p>
            ) : (
              <div className="space-y-2">
                {movements.map((m) => (
                  <div key={m.id} className="p-3 rounded-md border border-border text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{MOVEMENT_LABELS[m.movement_type] ?? m.movement_type}</span>
                      <span className={`font-semibold ${m.quantity_delta > 0 ? "text-success" : "text-destructive"}`}>
                        {m.quantity_delta > 0 ? "+" : ""}{m.quantity_delta}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-slate-400 text-xs">
                      <span>{m.reason}</span>
                      <span>Stock: {m.quantity_after}</span>
                    </div>
                    <p className="text-slate-400 text-xs mt-1">{formatDateTime(m.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
