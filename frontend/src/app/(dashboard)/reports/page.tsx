"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getRevenue, getBestSellers, getInventoryValuation } from "@/services/reports";
import { formatCurrency } from "@/utils/formatters";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function firstOfMonthStr() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

// ── Revenue tab ───────────────────────────────────────────────────────────────

function RevenueTab() {
  const [start, setStart] = useState(firstOfMonthStr());
  const [end, setEnd] = useState(todayStr());
  const [applied, setApplied] = useState({ start, end });

  const { data, isLoading } = useQuery({
    queryKey: ["report-revenue", applied],
    queryFn: () => getRevenue(applied),
  });

  const report = data?.data;

  const chartData = report?.rows.map((r) => ({
    date: r.date.slice(5),
    revenue: parseFloat(r.revenue),
    ventas: r.sale_count,
  })) ?? [];

  return (
    <div className="space-y-6">
      {/* Date controls */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Desde</Label>
          <Input type="date" className="w-40" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Hasta</Label>
          <Input type="date" className="w-40" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <Button onClick={() => setApplied({ start, end })}>Aplicar</Button>
      </div>

      {/* Summary cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 gap-4">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      ) : report ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Ingresos totales" value={formatCurrency(report.total_revenue)} />
          <StatCard label="Ventas totales" value={report.total_sales.toString()} />
          <StatCard
            label="Ticket promedio"
            value={report.total_sales > 0
              ? formatCurrency((parseFloat(report.total_revenue) / report.total_sales).toFixed(2))
              : "—"}
          />
          <StatCard label="Días con datos" value={report.rows.length.toString()} />
        </div>
      ) : null}

      {/* Line chart */}
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : chartData.length > 0 ? (
        <div className="rounded-lg border p-4">
          <p className="text-sm font-semibold mb-4">Ingresos diarios</p>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `S/${v}`} />
              <Tooltip formatter={(v) => formatCurrency(Number(v).toFixed(2))} />
              <Line
                type="monotone"
                dataKey="revenue"
                name="Ingresos"
                stroke="#0d9488"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : !isLoading ? (
        <p className="text-sm text-muted-foreground text-center py-10">Sin datos para el período seleccionado</p>
      ) : null}
    </div>
  );
}

// ── Best sellers tab ──────────────────────────────────────────────────────────

function BestSellersTab() {
  const [start, setStart] = useState(firstOfMonthStr());
  const [end, setEnd] = useState(todayStr());
  const [applied, setApplied] = useState({ start, end });

  const { data, isLoading } = useQuery({
    queryKey: ["report-best-sellers", applied],
    queryFn: () => getBestSellers({ ...applied, limit: 10 }),
  });

  const rows = data?.data.rows ?? [];

  const chartData = rows.map((r) => ({
    name: r.product_name.length > 20 ? r.product_name.slice(0, 20) + "…" : r.product_name,
    cantidad: r.total_quantity,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Desde</Label>
          <Input type="date" className="w-40" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Hasta</Label>
          <Input type="date" className="w-40" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <Button onClick={() => setApplied({ start, end })}>Aplicar</Button>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : chartData.length > 0 ? (
        <div className="rounded-lg border p-4">
          <p className="text-sm font-semibold mb-4">Top 10 productos más vendidos (unidades)</p>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={140} />
              <Tooltip />
              <Bar dataKey="cantidad" name="Unidades" fill="#0d9488" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground text-center py-10">Sin datos para el período seleccionado</p>
      )}

      {/* Table */}
      {!isLoading && rows.length > 0 && (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Producto</TableHead>
                <TableHead>SKU</TableHead>
                <TableHead className="text-right">Unidades</TableHead>
                <TableHead className="text-right">Ingresos</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, i) => (
                <TableRow key={row.product_id}>
                  <TableCell className="text-muted-foreground">{i + 1}</TableCell>
                  <TableCell className="font-medium">{row.product_name}</TableCell>
                  <TableCell className="font-mono text-sm text-muted-foreground">{row.sku}</TableCell>
                  <TableCell className="text-right">{row.total_quantity}</TableCell>
                  <TableCell className="text-right">{formatCurrency(row.total_revenue)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// ── Inventory valuation tab ───────────────────────────────────────────────────

function InventoryValuationTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["report-inventory-valuation"],
    queryFn: getInventoryValuation,
  });

  const report = data?.data;

  return (
    <div className="space-y-4">
      {isLoading ? (
        <Skeleton className="h-12 w-48" />
      ) : report ? (
        <div className="flex items-center gap-3">
          <p className="text-sm text-muted-foreground">Valorización total del inventario:</p>
          <Badge variant="default" className="text-base px-3 py-1">
            {formatCurrency(report.total_valuation)}
          </Badge>
        </div>
      ) : null}

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead className="text-right">Stock</TableHead>
              <TableHead className="text-right">Precio unit.</TableHead>
              <TableHead className="text-right">Valorización</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((_, j) => (
                    <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                  ))}
                </TableRow>
              ))
            ) : !report || report.rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center text-muted-foreground py-10">
                  Sin productos en inventario
                </TableCell>
              </TableRow>
            ) : (
              report.rows.map((row) => (
                <TableRow key={row.product_id}>
                  <TableCell className="font-medium">{row.product_name}</TableCell>
                  <TableCell className="font-mono text-sm text-muted-foreground">{row.sku}</TableCell>
                  <TableCell className="text-right">{row.quantity}</TableCell>
                  <TableCell className="text-right">{formatCurrency(row.unit_price)}</TableCell>
                  <TableCell className="text-right font-semibold">{formatCurrency(row.valuation)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ── Shared stat card ──────────────────────────────────────────────────────────

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-xl font-bold mt-1">{value}</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Reportes</h1>

      <Tabs defaultValue="revenue">
        <TabsList>
          <TabsTrigger value="revenue">Ingresos</TabsTrigger>
          <TabsTrigger value="best-sellers">Más vendidos</TabsTrigger>
          <TabsTrigger value="inventory">Valorización</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="mt-6">
          <RevenueTab />
        </TabsContent>
        <TabsContent value="best-sellers" className="mt-6">
          <BestSellersTab />
        </TabsContent>
        <TabsContent value="inventory" className="mt-6">
          <InventoryValuationTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
