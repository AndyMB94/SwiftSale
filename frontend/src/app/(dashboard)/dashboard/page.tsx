"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  CreditCard,
  ShoppingBag,
  TrendingUp,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getRevenue } from "@/services/reports";
import { getSales } from "@/services/sales";
import { getPayments } from "@/services/payments";
import { getInventory } from "@/services/products";
import { formatCurrency, formatDateTime } from "@/utils/formatters";
import { usePageTitle } from "@/hooks/usePageTitle";

function localDateStr(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function todayStr() {
  return localDateStr(new Date());
}

function nDaysAgoStr(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return localDateStr(d);
}

const STATUS_LABELS: Record<string, string> = {
  completed: "Completada",
  pending: "Pendiente",
  cancelled: "Cancelada",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  completed: "default",
  pending: "secondary",
  cancelled: "destructive",
};

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  icon: Icon,
  loading,
  highlight,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  loading?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-lg border p-5 flex items-start gap-4 ${highlight ? "border-amber-300 bg-amber-50" : ""}`}>
      <div className={`p-2 rounded-md ${highlight ? "bg-amber-100" : "bg-muted"}`}>
        <Icon size={18} className={highlight ? "text-amber-600" : "text-muted-foreground"} />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        {loading ? (
          <Skeleton className="h-7 w-24 mt-1" />
        ) : (
          <p className="text-2xl font-bold mt-0.5">{value}</p>
        )}
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  usePageTitle("Dashboard");

  const today = todayStr();
  const sevenDaysAgo = nDaysAgoStr(6);

  const { data: todayRevData, isLoading: loadingToday } = useQuery({
    queryKey: ["dashboard-revenue-today", today],
    queryFn: () => getRevenue({ start: today, end: today }),
  });

  const { data: weekRevData, isLoading: loadingWeek } = useQuery({
    queryKey: ["dashboard-revenue-week", sevenDaysAgo, today],
    queryFn: () => getRevenue({ start: sevenDaysAgo, end: today }),
  });

  const { data: salesData, isLoading: loadingSales } = useQuery({
    queryKey: ["dashboard-recent-sales"],
    queryFn: () => getSales({ page: 1, page_size: 5 }),
  });

  const { data: lowStockData, isLoading: loadingStock } = useQuery({
    queryKey: ["dashboard-low-stock"],
    queryFn: () => getInventory({ low_stock_only: true, page_size: 5 }),
  });

  const { data: pendingPayData } = useQuery({
    queryKey: ["dashboard-pending-payments"],
    queryFn: () => getPayments({ status: "pending", page_size: 1 }),
  });

  const todayRev = todayRevData?.data;
  const weekRev = weekRevData?.data;
  const recentSales = salesData?.data?.results ?? [];
  const lowStockItems = lowStockData?.data?.results ?? [];
  const lowStockCount = lowStockData?.data?.count ?? 0;
  const pendingCount = pendingPayData?.data?.count ?? 0;

  const chartData =
    weekRev?.rows.map((r) => ({
      date: r.date.slice(5),
      revenue: parseFloat(r.revenue),
    })) ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Ingresos hoy"
          value={todayRev ? formatCurrency(todayRev.total_revenue) : "—"}
          icon={TrendingUp}
          loading={loadingToday}
        />
        <StatCard
          label="Ventas hoy"
          value={todayRev ? todayRev.total_sales.toString() : "—"}
          icon={ShoppingBag}
          loading={loadingToday}
        />
        <StatCard
          label="Stock bajo"
          value={lowStockCount.toString()}
          icon={AlertTriangle}
          loading={loadingStock}
          highlight={lowStockCount > 0}
        />
        <StatCard
          label="Pagos pendientes"
          value={pendingCount.toString()}
          icon={CreditCard}
          loading={false}
          highlight={pendingCount > 0}
        />
      </div>

      {/* Revenue chart */}
      <div className="rounded-lg border p-5">
        <p className="text-sm font-semibold mb-4">Ingresos — últimos 7 días</p>
        {loadingWeek ? (
          <Skeleton className="h-48 w-full" />
        ) : chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
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
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-10">
            Sin ventas en los últimos 7 días
          </p>
        )}
      </div>

      {/* Bottom grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent sales */}
        <div className="rounded-lg border">
          <div className="px-4 py-3 border-b">
            <p className="text-sm font-semibold">Últimas ventas</p>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fecha</TableHead>
                <TableHead>Cajero</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead className="text-center">Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loadingSales ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : recentSales.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={4}
                    className="text-center text-muted-foreground py-8 text-sm"
                  >
                    Sin ventas registradas
                  </TableCell>
                </TableRow>
              ) : (
                recentSales.map((sale) => (
                  <TableRow key={sale.id}>
                    <TableCell className="text-xs text-muted-foreground">
                      {formatDateTime(sale.created_at)}
                    </TableCell>
                    <TableCell className="text-sm">{sale.cashier_name}</TableCell>
                    <TableCell className="text-right text-sm font-medium">
                      {formatCurrency(sale.total)}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant={STATUS_VARIANTS[sale.status] ?? "outline"}>
                        {STATUS_LABELS[sale.status] ?? sale.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Low stock */}
        <div className="rounded-lg border">
          <div className="px-4 py-3 border-b flex items-center justify-between">
            <p className="text-sm font-semibold">Alertas de stock bajo</p>
            {lowStockCount > 0 && (
              <Badge variant="destructive">{lowStockCount}</Badge>
            )}
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead className="text-right">Stock</TableHead>
                <TableHead className="text-right">Mínimo</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loadingStock ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 3 }).map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : lowStockItems.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={3}
                    className="text-center text-muted-foreground py-8 text-sm"
                  >
                    Todo el stock está en niveles normales
                  </TableCell>
                </TableRow>
              ) : (
                lowStockItems.map((item) => (
                  <TableRow key={item.product_id}>
                    <TableCell>
                      <p className="text-sm font-medium">{item.product_name}</p>
                      <p className="text-xs text-muted-foreground font-mono">{item.sku}</p>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="text-amber-600 font-semibold">
                        {item.quantity}
                      </span>
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground text-sm">
                      {item.low_stock_threshold}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
