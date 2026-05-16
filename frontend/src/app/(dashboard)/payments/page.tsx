"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { usePageTitle } from "@/hooks/usePageTitle";
import { ChevronLeft, ChevronRight } from "lucide-react";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getPayments } from "@/services/payments";
import { formatCurrency, formatDateTime } from "@/utils/formatters";
import type { PaymentListItem } from "@/types/sales";

const PAGE_SIZE = 20;

const METHOD_LABELS: Record<string, string> = {
  cash: "Efectivo",
  card: "Tarjeta",
  yape: "Yape",
  plin: "Plin",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  paid: "Pagado",
  failed: "Fallido",
  refunded: "Reembolsado",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  paid: "default",
  pending: "secondary",
  failed: "destructive",
  refunded: "outline",
};

export default function PaymentsPage() {
  usePageTitle("Pagos");
  const [methodFilter, setMethodFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [methodFilter, statusFilter, dateFrom, dateTo]);

  const { data, isLoading } = useQuery({
    queryKey: ["payments", { methodFilter, statusFilter, dateFrom, dateTo, page }],
    queryFn: () =>
      getPayments({
        method: methodFilter === "all" ? undefined : methodFilter,
        status: statusFilter === "all" ? undefined : statusFilter,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const payments = data?.data;
  const hasFilters =
    methodFilter !== "all" || statusFilter !== "all" || dateFrom || dateTo;

  const from = payments ? (payments.page - 1) * payments.page_size + 1 : 0;
  const to = payments
    ? Math.min(payments.page * payments.page_size, payments.count)
    : 0;

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Pagos</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Método</Label>
          <Select value={methodFilter} onValueChange={setMethodFilter}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="cash">Efectivo</SelectItem>
              <SelectItem value="card">Tarjeta</SelectItem>
              <SelectItem value="yape">Yape</SelectItem>
              <SelectItem value="plin">Plin</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Estado</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="paid">Pagado</SelectItem>
              <SelectItem value="pending">Pendiente</SelectItem>
              <SelectItem value="failed">Fallido</SelectItem>
              <SelectItem value="refunded">Reembolsado</SelectItem>
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

        {hasFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setMethodFilter("all");
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
              <TableHead>Método</TableHead>
              <TableHead className="text-right">Monto</TableHead>
              <TableHead className="text-center">Estado</TableHead>
              <TableHead>Referencia</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !payments || payments.results.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-muted-foreground py-10"
                >
                  {hasFilters
                    ? "Sin resultados para los filtros aplicados"
                    : "No hay pagos registrados"}
                </TableCell>
              </TableRow>
            ) : (
              payments.results.map((payment: PaymentListItem) => (
                <TableRow key={payment.id}>
                  <TableCell className="text-sm">
                    {formatDateTime(payment.created_at)}
                  </TableCell>
                  <TableCell>{payment.cashier_name}</TableCell>
                  <TableCell>
                    {METHOD_LABELS[payment.method] ?? payment.method}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(payment.amount)}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge
                      variant={STATUS_VARIANTS[payment.status] ?? "outline"}
                    >
                      {STATUS_LABELS[payment.status] ?? payment.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-xs font-mono">
                    {payment.provider_ref ?? "—"}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {/* Pagination */}
        {payments && payments.count > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t text-sm text-muted-foreground">
            <span>
              Mostrando {from}–{to} de {payments.count} pagos
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
                disabled={page === payments.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
