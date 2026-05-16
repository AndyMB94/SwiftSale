"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ChevronLeft, ChevronRight, Eye, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { Separator } from "@/components/ui/separator";
import { cancelSale, getSale, getSales } from "@/services/sales";
import { formatCurrency, formatDateTime } from "@/utils/formatters";
import type { Sale, SaleListItem } from "@/types/sales";

const PAGE_SIZE = 20;

const STATUS_LABELS: Record<string, string> = {
  completed: "Completada",
  pending: "Pendiente",
  cancelled: "Cancelada",
};

const METHOD_LABELS: Record<string, string> = {
  cash: "Efectivo",
  card: "Tarjeta",
  yape: "Yape",
  plin: "Plin",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  completed: "default",
  pending: "secondary",
  cancelled: "destructive",
};

export default function SalesPage() {
  const qc = useQueryClient();

  const [statusFilter, setStatusFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [statusFilter, dateFrom, dateTo]);

  const { data, isLoading } = useQuery({
    queryKey: ["sales", { statusFilter, dateFrom, dateTo, page }],
    queryFn: () =>
      getSales({
        status: statusFilter === "all" ? undefined : statusFilter,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const { data: detailData, isLoading: detailLoading } = useQuery({
    queryKey: ["sale", selectedId],
    queryFn: () => getSale(selectedId!),
    enabled: !!selectedId,
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => cancelSale(id),
    onSuccess: () => {
      toast.success("Venta cancelada");
      qc.invalidateQueries({ queryKey: ["sales"] });
      qc.invalidateQueries({ queryKey: ["sale", selectedId] });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(detail ?? "Error al cancelar la venta");
    },
  });

  const sales = data?.data;
  const detail: Sale | undefined = detailData?.data;

  function openDetail(id: string) {
    setSelectedId(id);
    setSheetOpen(true);
  }

  function handleCancel(id: string) {
    if (!confirm("¿Cancelar esta venta? Se revertirá el stock.")) return;
    cancelMutation.mutate(id);
  }

  const from = sales ? (sales.page - 1) * sales.page_size + 1 : 0;
  const to = sales ? Math.min(sales.page * sales.page_size, sales.count) : 0;

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Historial de ventas</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Estado</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="completed">Completadas</SelectItem>
              <SelectItem value="pending">Pendientes</SelectItem>
              <SelectItem value="cancelled">Canceladas</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Desde</Label>
          <Input
            type="date"
            className="w-40"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
        </div>

        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Hasta</Label>
          <Input
            type="date"
            className="w-40"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
        </div>

        {(dateFrom || dateTo || statusFilter !== "all") && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setStatusFilter("all");
              setDateFrom("");
              setDateTo("");
            }}
          >
            Limpiar filtros
          </Button>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha y hora</TableHead>
              <TableHead>Cajero</TableHead>
              <TableHead className="text-center">Productos</TableHead>
              <TableHead>Método</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-center">Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !sales || sales.results.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="text-center text-muted-foreground py-10"
                >
                  {statusFilter !== "all" || dateFrom || dateTo
                    ? "Sin resultados para los filtros aplicados"
                    : "No hay ventas registradas"}
                </TableCell>
              </TableRow>
            ) : (
              sales.results.map((sale: SaleListItem) => (
                <TableRow key={sale.id}>
                  <TableCell className="text-sm">
                    {formatDateTime(sale.created_at)}
                  </TableCell>
                  <TableCell>{sale.cashier_name}</TableCell>
                  <TableCell className="text-center">
                    {sale.item_count}
                  </TableCell>
                  <TableCell>
                    {sale.payment
                      ? METHOD_LABELS[sale.payment.method] ?? sale.payment.method
                      : "—"}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(sale.total)}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={STATUS_VARIANTS[sale.status] ?? "outline"}>
                      {STATUS_LABELS[sale.status] ?? sale.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => openDetail(sale.id)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                      {sale.status === "completed" && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleCancel(sale.id)}
                          disabled={cancelMutation.isPending}
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {sales && sales.count > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t text-sm text-muted-foreground">
            <span>
              Mostrando {from}–{to} de {sales.count} ventas
            </span>
            <div className="flex gap-1">
              <Button
                size="icon"
                variant="ghost"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                disabled={page === sales.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Detail slide-over */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto" aria-describedby={undefined}>
          <SheetHeader>
            <SheetTitle>Detalle de venta</SheetTitle>
          </SheetHeader>

          {detailLoading || !detail ? (
            <div className="mt-6 space-y-3 px-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          ) : (
            <div className="px-4 pb-6 space-y-6">
              {/* Header info */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Fecha</p>
                  <p className="font-medium">
                    {formatDateTime(detail.created_at)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Estado</p>
                  <Badge variant={STATUS_VARIANTS[detail.status] ?? "outline"}>
                    {STATUS_LABELS[detail.status] ?? detail.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-muted-foreground">Cajero</p>
                  <p className="font-medium">{detail.cashier_name}</p>
                </div>
                {detail.payment && (
                  <div>
                    <p className="text-muted-foreground">Método de pago</p>
                    <p className="font-medium">
                      {METHOD_LABELS[detail.payment.method] ??
                        detail.payment.method}
                    </p>
                  </div>
                )}
              </div>

              <Separator />

              {/* Items */}
              <div>
                <p className="text-sm font-semibold mb-3">Productos</p>
                <div className="space-y-2">
                  {detail.items.map((item) => (
                    <div key={item.id} className="flex justify-between text-sm">
                      <div>
                        <p className="font-medium">{item.product_name}</p>
                        <p className="text-muted-foreground text-xs">
                          {item.sku} · {item.quantity} ×{" "}
                          {formatCurrency(item.unit_price)}
                        </p>
                      </div>
                      <p className="font-medium">
                        {formatCurrency(item.subtotal)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Totals */}
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>{formatCurrency(detail.subtotal)}</span>
                </div>
                {parseFloat(detail.discount) > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Descuento</span>
                    <span>−{formatCurrency(detail.discount)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">IGV (18%)</span>
                  <span>{formatCurrency(detail.tax)}</span>
                </div>
                <div className="flex justify-between font-bold text-base pt-1">
                  <span>Total</span>
                  <span>{formatCurrency(detail.total)}</span>
                </div>
              </div>

              {/* Cancel action */}
              {detail.status === "completed" && (
                <>
                  <Separator />
                  <Button
                    variant="destructive"
                    className="w-full"
                    disabled={cancelMutation.isPending}
                    onClick={() => handleCancel(detail.id)}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Cancelar venta
                  </Button>
                </>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
