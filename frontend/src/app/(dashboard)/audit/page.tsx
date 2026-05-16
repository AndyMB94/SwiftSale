"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
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
import { getAuditLogs } from "@/services/audit";
import { formatDateTime } from "@/utils/formatters";
import type { AuditLog } from "@/types/audit";

const ACTION_LABELS: Record<string, string> = {
  price_change: "Cambio de precio",
  stock_adjustment: "Ajuste de stock",
  sale_cancelled: "Venta cancelada",
  login_failed: "Login fallido",
  user_deactivated: "Usuario desactivado",
  document_voided: "Documento anulado",
};

const TARGET_TYPES = [
  "product",
  "inventory",
  "sale",
  "user",
  "billing_document",
];

export default function AuditPage() {
  const [action, setAction] = useState("all");
  const [targetType, setTargetType] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [applied, setApplied] = useState({
    action: "all",
    targetType: "all",
    dateFrom: "",
    dateTo: "",
  });

  function apply() {
    setApplied({ action, targetType, dateFrom, dateTo });
  }

  function clear() {
    setAction("all");
    setTargetType("all");
    setDateFrom("");
    setDateTo("");
    setApplied({ action: "all", targetType: "all", dateFrom: "", dateTo: "" });
  }

  const hasFilters =
    applied.action !== "all" ||
    applied.targetType !== "all" ||
    applied.dateFrom ||
    applied.dateTo;

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", applied],
    queryFn: () =>
      getAuditLogs({
        action: applied.action !== "all" ? applied.action : undefined,
        target_type: applied.targetType !== "all" ? applied.targetType : undefined,
        start: applied.dateFrom || undefined,
        end: applied.dateTo || undefined,
        limit: 200,
      }),
  });

  const logs: AuditLog[] = data?.data ?? [];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Log de auditoría</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Acción</Label>
          <Select value={action} onValueChange={setAction}>
            <SelectTrigger className="w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas</SelectItem>
              {Object.entries(ACTION_LABELS).map(([k, v]) => (
                <SelectItem key={k} value={k}>{v}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Objeto</Label>
          <Select value={targetType} onValueChange={setTargetType}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {TARGET_TYPES.map((t) => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
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

        <Button onClick={apply}>Aplicar</Button>
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clear}>
            Limpiar
          </Button>
        )}
      </div>

      <p className="text-xs text-muted-foreground">
        {isLoading ? "Cargando…" : `${logs.length} registros`}
      </p>

      {/* Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha y hora</TableHead>
              <TableHead>Acción</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Objeto</TableHead>
              <TableHead>ID objetivo</TableHead>
              <TableHead>IP</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-muted-foreground py-10"
                >
                  {hasFilters
                    ? "Sin registros para los filtros aplicados"
                    : "No hay registros de auditoría"}
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm text-nowrap">
                    {formatDateTime(log.created_at)}
                  </TableCell>
                  <TableCell className="text-sm font-medium">
                    {ACTION_LABELS[log.action] ?? log.action}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground font-mono">
                    {log.actor_id ? log.actor_id.slice(0, 8) + "…" : "sistema"}
                  </TableCell>
                  <TableCell className="text-sm">{log.target_type}</TableCell>
                  <TableCell className="text-sm font-mono text-muted-foreground">
                    {log.target_id.slice(0, 8)}…
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {log.ip_address ?? "—"}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
