"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  CheckCircle2,
  Minus,
  Plus,
  QrCode,
  Search,
  ShoppingCart,
  Trash2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { getProducts } from "@/services/products";
import { createCheckout } from "@/services/checkout";
import { usePosStore } from "@/store/posStore";
import { useAuthStore } from "@/store/authStore";
import { formatCurrency } from "@/utils/formatters";
import type { PaymentMethod, Sale } from "@/types/sales";

// IGV matches the backend constant (18%)
const IGV_RATE = 0.18;

type Step = "cart" | "cash" | "card" | "qr" | "processing" | "success";

const METHOD_LABELS: Record<PaymentMethod, string> = {
  cash: "Efectivo",
  card: "Tarjeta",
  yape: "Yape",
  plin: "Plin",
};

export default function PosPage() {
  const user = useAuthStore((s) => s.user);
  const { items, discount, paymentMethod, addItem, removeItem, updateQuantity, setDiscount, setPaymentMethod, clearCart } = usePosStore();

  const [search, setSearch] = useState("");
  const [step, setStep] = useState<Step>("cart");
  const [cashReceived, setCashReceived] = useState("");
  const [completedSale, setCompletedSale] = useState<Sale | null>(null);
  const [countdown, setCountdown] = useState(120);
  const idempotencyKey = useRef(crypto.randomUUID());

  // ── Product query (fetch all for instant client-side filtering) ────────────

  const { data: productsRes, isLoading: loadingProducts } = useQuery({
    queryKey: ["pos-products"],
    queryFn: () => getProducts({ page_size: 200 }),
    staleTime: 5 * 60 * 1000,
  });

  const allProducts = productsRes?.data.results ?? [];

  const filtered = useMemo(() => {
    if (!search.trim()) return allProducts;
    const q = search.toLowerCase();
    return allProducts.filter(
      (p) => p.name.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q),
    );
  }, [allProducts, search]);

  // ── Totals ─────────────────────────────────────────────────────────────────

  const subtotal = useMemo(
    () => items.reduce((acc, i) => acc + parseFloat(i.unit_price) * i.quantity, 0),
    [items],
  );
  const discountNum = Math.min(parseFloat(discount) || 0, subtotal);
  const tax = Math.round(subtotal * IGV_RATE * 100) / 100;
  const total = Math.max(0, subtotal - discountNum + tax);
  const change = parseFloat(cashReceived) - total;

  // ── Countdown for Yape/Plin QR ────────────────────────────────────────────

  useEffect(() => {
    if (step !== "qr") return;
    if (countdown <= 0) {
      toast.error("Tiempo expirado. Intenta de nuevo.");
      setStep("cart");
      return;
    }
    const timer = setInterval(() => setCountdown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [step, countdown]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  function startPayment(method: PaymentMethod) {
    if (items.length === 0) {
      toast.error("El carrito está vacío");
      return;
    }
    idempotencyKey.current = crypto.randomUUID();
    setPaymentMethod(method);
    setCashReceived("");
    if (method === "cash") {
      setStep("cash");
    } else if (method === "card") {
      setStep("card");
    } else {
      setCountdown(120);
      setStep("qr");
    }
  }

  async function submitSale() {
    setStep("processing");
    try {
      const res = await createCheckout({
        items: items.map((i) => ({ product_id: i.product.id, quantity: i.quantity })),
        discount: discountNum > 0 ? discountNum.toFixed(2) : undefined,
        method: paymentMethod!,
        idempotency_key: idempotencyKey.current,
      });
      setCompletedSale(res.data.sale);
      setStep("success");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail ?? "Error al procesar la venta");
      setStep(
        paymentMethod === "cash" ? "cash" : paymentMethod === "card" ? "card" : "qr",
      );
    }
  }

  function resetPos() {
    clearCart();
    setDiscount("0.00");
    setStep("cart");
    setCompletedSale(null);
    setCashReceived("");
  }

  function cancelPayment() {
    setStep("cart");
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="h-screen bg-[#111827] flex flex-col overflow-hidden">

      {/* Top bar */}
      <div className="h-14 bg-slate-900 border-b border-slate-700 flex items-center px-5 gap-4 shrink-0">
        <span className="text-white font-bold text-lg tracking-tight">
          Swift<span className="text-primary">Sale</span>
          <span className="text-slate-500 font-normal text-sm ml-2">POS</span>
        </span>
        <div className="flex-1" />
        {user?.role !== "cashier" && (
          <a
            href="/dashboard"
            className="text-slate-400 hover:text-slate-200 text-sm transition-colors"
          >
            ← Volver al dashboard
          </a>
        )}
        <span className="text-slate-500 text-sm">{user?.full_name}</span>
      </div>

      {/* Main area */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Left: product grid ── */}
        <div className="flex-1 flex flex-col overflow-hidden border-r border-slate-700">
          {/* Search */}
          <div className="p-4 border-b border-slate-700">
            <div className="relative">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="Buscar producto o SKU..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 bg-slate-800 border-slate-600 text-white placeholder:text-slate-500 focus-visible:ring-primary"
              />
            </div>
          </div>

          {/* Grid */}
          <div className="flex-1 overflow-y-auto p-4">
            {loadingProducts ? (
              <div className="grid grid-cols-3 xl:grid-cols-4 gap-3">
                {Array.from({ length: 12 }).map((_, i) => (
                  <Skeleton key={i} className="h-24 bg-slate-800" />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-slate-500 text-sm text-center pt-12">
                {search ? "Sin resultados" : "No hay productos disponibles"}
              </p>
            ) : (
              <div className="grid grid-cols-3 xl:grid-cols-4 gap-3">
                {filtered.map((product) => {
                  const inCart = items.find((i) => i.product.id === product.id);
                  return (
                    <button
                      key={product.id}
                      onClick={() => addItem(product)}
                      className="relative p-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                      {inCart && (
                        <span className="absolute top-2 right-2 bg-primary text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                          {inCart.quantity}
                        </span>
                      )}
                      <p className="text-white text-sm font-medium line-clamp-2 pr-5 leading-snug">
                        {product.name}
                      </p>
                      <p className="text-slate-500 text-xs mt-1 font-mono">{product.sku}</p>
                      <p className="text-primary text-sm font-bold mt-2">
                        {formatCurrency(product.price)}
                      </p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── Right: cart / payment panel ── */}
        <div className="w-96 shrink-0 bg-slate-900 flex flex-col">

          {/* ── STEP: cart ── */}
          {step === "cart" && (
            <>
              {/* Cart header */}
              <div className="px-5 py-4 border-b border-slate-700 flex items-center gap-2">
                <ShoppingCart size={16} className="text-slate-400" />
                <span className="text-white font-semibold text-sm">
                  Carrito
                </span>
                {items.length > 0 && (
                  <span className="ml-auto text-xs text-slate-500">
                    {items.length} producto{items.length !== 1 ? "s" : ""}
                  </span>
                )}
              </div>

              {/* Cart items */}
              <div className="flex-1 overflow-y-auto">
                {items.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full gap-3 text-slate-600">
                    <ShoppingCart size={40} strokeWidth={1.5} />
                    <p className="text-sm">Selecciona productos del catálogo</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800">
                    {items.map((item) => (
                      <div key={item.product.id} className="px-5 py-3 flex items-center gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-sm font-medium truncate">
                            {item.product.name}
                          </p>
                          <p className="text-slate-500 text-xs">
                            {formatCurrency(item.unit_price)} c/u
                          </p>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                            className="w-6 h-6 rounded bg-slate-700 hover:bg-slate-600 flex items-center justify-center text-white transition-colors"
                          >
                            <Minus size={11} />
                          </button>
                          <span className="text-white text-sm font-semibold w-6 text-center tabular-nums">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                            className="w-6 h-6 rounded bg-slate-700 hover:bg-slate-600 flex items-center justify-center text-white transition-colors"
                          >
                            <Plus size={11} />
                          </button>
                        </div>
                        <span className="text-white text-sm font-semibold w-16 text-right tabular-nums shrink-0">
                          {formatCurrency(parseFloat(item.unit_price) * item.quantity)}
                        </span>
                        <button
                          onClick={() => removeItem(item.product.id)}
                          className="text-slate-600 hover:text-red-400 transition-colors ml-1"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Totals + discount */}
              <div className="border-t border-slate-700 px-5 py-4 space-y-3">
                <div className="flex items-center gap-2">
                  <label className="text-slate-400 text-xs shrink-0">Descuento (S/)</label>
                  <Input
                    type="number"
                    min="0"
                    step="0.10"
                    value={discount}
                    onChange={(e) => setDiscount(e.target.value)}
                    className="h-8 text-sm bg-slate-800 border-slate-600 text-white text-right"
                  />
                </div>
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between text-slate-400">
                    <span>Subtotal</span>
                    <span className="tabular-nums">{formatCurrency(subtotal)}</span>
                  </div>
                  {discountNum > 0 && (
                    <div className="flex justify-between text-amber-400">
                      <span>Descuento</span>
                      <span className="tabular-nums">− {formatCurrency(discountNum)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-slate-400">
                    <span>IGV (18%)</span>
                    <span className="tabular-nums">{formatCurrency(tax)}</span>
                  </div>
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-slate-700">
                  <span className="text-white font-bold text-base">Total</span>
                  <span className="text-white font-bold text-2xl tabular-nums">
                    {formatCurrency(total)}
                  </span>
                </div>
              </div>

              {/* Payment method buttons */}
              <div className="px-5 pb-5 grid grid-cols-2 gap-2">
                {(["cash", "card", "yape", "plin"] as PaymentMethod[]).map((m) => (
                  <Button
                    key={m}
                    onClick={() => startPayment(m)}
                    disabled={items.length === 0}
                    className="h-12 bg-slate-700 hover:bg-primary hover:text-white text-slate-200 font-semibold transition-colors disabled:opacity-30"
                    variant="ghost"
                  >
                    {METHOD_LABELS[m]}
                  </Button>
                ))}
              </div>
            </>
          )}

          {/* ── STEP: cash ── */}
          {step === "cash" && (
            <div className="flex flex-col h-full px-5 py-6 gap-5">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold">Pago en Efectivo</h3>
                <button onClick={cancelPayment} className="text-slate-500 hover:text-slate-300">
                  <X size={18} />
                </button>
              </div>

              <div className="bg-slate-800 rounded-xl p-5 text-center">
                <p className="text-slate-400 text-xs mb-1">Total a cobrar</p>
                <p className="text-white text-4xl font-bold tabular-nums">
                  {formatCurrency(total)}
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-slate-400 text-sm">Efectivo recibido</label>
                <Input
                  type="number"
                  min="0"
                  step="0.10"
                  placeholder="0.00"
                  value={cashReceived}
                  onChange={(e) => setCashReceived(e.target.value)}
                  autoFocus
                  className="h-12 text-xl text-right bg-slate-800 border-slate-600 text-white"
                />
              </div>

              {cashReceived && (
                <div className={`rounded-lg p-4 text-center ${change >= 0 ? "bg-emerald-900/40" : "bg-red-900/40"}`}>
                  <p className="text-xs mb-1 text-slate-400">
                    {change >= 0 ? "Vuelto" : "Monto insuficiente"}
                  </p>
                  <p className={`text-2xl font-bold tabular-nums ${change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {formatCurrency(Math.abs(change))}
                  </p>
                </div>
              )}

              <div className="mt-auto space-y-2">
                <Button
                  onClick={submitSale}
                  disabled={!cashReceived || change < 0}
                  className="w-full h-12 text-base font-semibold"
                >
                  Confirmar venta
                </Button>
                <Button
                  variant="ghost"
                  onClick={cancelPayment}
                  className="w-full text-slate-500 hover:text-slate-300"
                >
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          {/* ── STEP: card ── */}
          {step === "card" && (
            <div className="flex flex-col h-full px-5 py-6 gap-5">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold">Pago con Tarjeta</h3>
                <button onClick={cancelPayment} className="text-slate-500 hover:text-slate-300">
                  <X size={18} />
                </button>
              </div>

              <div className="bg-slate-800 rounded-xl p-5 text-center">
                <p className="text-slate-400 text-xs mb-1">Total a cobrar</p>
                <p className="text-white text-4xl font-bold tabular-nums">
                  {formatCurrency(total)}
                </p>
              </div>

              <div className="flex-1 flex items-center justify-center">
                <p className="text-slate-400 text-sm text-center px-4">
                  Procesa el pago en el terminal POS y confirma cuando esté aprobado.
                </p>
              </div>

              <div className="space-y-2">
                <Button onClick={submitSale} className="w-full h-12 text-base font-semibold">
                  Confirmar venta
                </Button>
                <Button
                  variant="ghost"
                  onClick={cancelPayment}
                  className="w-full text-slate-500 hover:text-slate-300"
                >
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          {/* ── STEP: qr (Yape / Plin) ── */}
          {step === "qr" && (
            <div className="flex flex-col h-full px-5 py-6 gap-5">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-semibold">
                  Pago por {paymentMethod === "yape" ? "Yape" : "Plin"}
                </h3>
                <button onClick={cancelPayment} className="text-slate-500 hover:text-slate-300">
                  <X size={18} />
                </button>
              </div>

              <p className="text-slate-400 text-xs text-center">
                Solicita al cliente que escanee el código QR
              </p>

              {/* QR placeholder */}
              <div className="bg-white rounded-2xl p-5 w-52 h-52 mx-auto flex items-center justify-center">
                <QrCode size={168} className="text-gray-900" />
              </div>

              <div className="text-center">
                <p className="text-slate-400 text-xs">Monto</p>
                <p className="text-white text-3xl font-bold tabular-nums">
                  {formatCurrency(total)}
                </p>
              </div>

              {/* Countdown */}
              <div className="text-center">
                <p className="text-slate-500 text-xs mb-1">Tiempo restante</p>
                <p className={`text-xl font-mono font-semibold tabular-nums ${countdown <= 30 ? "text-red-400" : "text-emerald-400"}`}>
                  {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, "0")}
                </p>
              </div>

              <div className="mt-auto space-y-2">
                <Button onClick={submitSale} className="w-full h-12 text-base font-semibold">
                  Confirmar pago recibido
                </Button>
                <Button
                  variant="ghost"
                  onClick={cancelPayment}
                  className="w-full text-slate-500 hover:text-slate-300"
                >
                  Cancelar
                </Button>
              </div>
            </div>
          )}

          {/* ── STEP: processing ── */}
          {step === "processing" && (
            <div className="flex flex-col h-full items-center justify-center gap-4">
              <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin" />
              <p className="text-slate-400 text-sm">Procesando venta...</p>
            </div>
          )}

          {/* ── STEP: success ── */}
          {step === "success" && completedSale && (
            <div className="flex flex-col h-full px-5 py-8 items-center gap-6">
              <CheckCircle2 size={64} className="text-emerald-400 shrink-0" />
              <div className="text-center">
                <p className="text-white font-bold text-xl">Venta completada</p>
                <p className="text-slate-400 text-sm mt-1">
                  {new Date(completedSale.created_at).toLocaleTimeString("es-PE", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>

              <div className="bg-slate-800 rounded-xl p-5 w-full space-y-3 text-sm">
                <div className="flex justify-between text-slate-400">
                  <span>Subtotal</span>
                  <span className="tabular-nums">{formatCurrency(completedSale.subtotal)}</span>
                </div>
                {parseFloat(completedSale.discount) > 0 && (
                  <div className="flex justify-between text-amber-400">
                    <span>Descuento</span>
                    <span className="tabular-nums">− {formatCurrency(completedSale.discount)}</span>
                  </div>
                )}
                <div className="flex justify-between text-slate-400">
                  <span>IGV (18%)</span>
                  <span className="tabular-nums">{formatCurrency(completedSale.tax)}</span>
                </div>
                <div className="flex justify-between text-white font-bold text-base pt-2 border-t border-slate-700">
                  <span>Total</span>
                  <span className="tabular-nums">{formatCurrency(completedSale.total)}</span>
                </div>
                <div className="flex justify-between text-slate-400 pt-1">
                  <span>Método</span>
                  <span>{paymentMethod ? METHOD_LABELS[paymentMethod] : "—"}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Productos</span>
                  <span>{completedSale.items.length}</span>
                </div>
              </div>

              <Button onClick={resetPos} className="w-full h-12 text-base font-semibold mt-auto">
                Nueva venta
              </Button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
