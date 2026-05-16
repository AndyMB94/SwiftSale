"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/services/auth";
import { useAuthStore } from "@/store/authStore";
import type { UserRole } from "@/types/auth";

const ROLE_REDIRECT: Record<UserRole, string> = {
  admin: "/dashboard",
  supervisor: "/dashboard",
  cashier: "/pos",
};

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await login({ email, password });
      setUser(data.user);
      router.push(ROLE_REDIRECT[data.user.role]);
    } catch {
      setError("Credenciales incorrectas. Verifica tu email y contraseña.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Brand panel */}
      <div className="hidden lg:flex lg:w-[58%] relative bg-[#0F172A] flex-col overflow-hidden">
        {/* Teal accent bar */}
        <div className="absolute left-0 top-0 bottom-0 w-0.75 bg-primary" />

        {/* Subtle grid texture */}
        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage: [
              "linear-gradient(rgba(13,148,136,1) 1px, transparent 1px)",
              "linear-gradient(90deg, rgba(13,148,136,1) 1px, transparent 1px)",
            ].join(", "),
            backgroundSize: "52px 52px",
          }}
        />

        {/* Glow spot */}
        <div className="absolute top-[-10%] left-[-5%] w-120 h-120 rounded-full bg-primary/10 blur-[120px] pointer-events-none" />

        <div className="relative z-10 flex flex-col justify-between h-full p-14">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center shrink-0">
              <span className="text-white font-bold text-[17px] leading-none">S</span>
            </div>
            <span className="text-white font-semibold text-xl tracking-tight">
              SwiftSale
            </span>
          </div>

          {/* Main copy */}
          <div className="space-y-8 max-w-md">
            <div className="space-y-3">
              <p className="text-primary text-xs font-semibold tracking-[0.2em] uppercase">
                Sistema de gestión retail
              </p>
              <h1 className="text-white text-[2.6rem] font-bold leading-[1.15] tracking-tight">
                Control total<br />de tu negocio.
              </h1>
            </div>

            <p className="text-slate-400 text-[15px] leading-relaxed">
              POS, inventario, facturación electrónica SUNAT y reportes — todo en una sola plataforma.
            </p>

            <div className="space-y-3.5 pt-1">
              {[
                "Punto de venta optimizado para velocidad",
                "Facturación electrónica SUNAT",
                "Inventario con alertas de stock bajo",
                "Reportes de ventas en tiempo real",
              ].map((feat) => (
                <div key={feat} className="flex items-center gap-3">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                  <span className="text-slate-400 text-sm">{feat}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="text-slate-600 text-xs">SwiftSale v1.0 &mdash; Uso interno</p>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex flex-col items-center justify-center bg-background px-8 py-12">
        <div className="w-full max-w-85 space-y-8">
          {/* Mobile logo */}
          <div className="flex lg:hidden items-center gap-2.5 mb-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="text-white font-bold text-sm">S</span>
            </div>
            <span className="font-semibold text-lg tracking-tight">SwiftSale</span>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-[1.6rem] font-bold tracking-tight text-foreground">
              Iniciar sesión
            </h2>
            <p className="text-sm text-slate-500">
              Ingresa tus credenciales para acceder al sistema.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="usuario@empresa.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Contraseña</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            {error && (
              <p className="text-sm text-destructive font-medium">{error}</p>
            )}

            <Button type="submit" className="w-full h-10" disabled={loading}>
              {loading ? "Ingresando..." : "Ingresar al sistema"}
            </Button>
          </form>

          <p className="text-center text-xs text-slate-400 leading-relaxed">
            ¿Sin acceso? Contacta al administrador del sistema.
          </p>
        </div>
      </div>
    </div>
  );
}
