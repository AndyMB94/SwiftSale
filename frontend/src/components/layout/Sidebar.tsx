"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  Boxes,
  CreditCard,
  FileText,
  LayoutDashboard,
  LogOut,
  Monitor,
  Package,
  Receipt,
  ShieldCheck,
  Users,
} from "lucide-react";
import { logout } from "@/services/auth";
import { useAuthStore } from "@/store/authStore";
import type { UserRole } from "@/types/auth";

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
}

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  admin: [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/pos", label: "Punto de Venta", icon: Monitor },
    { href: "/products", label: "Productos", icon: Package },
    { href: "/inventory", label: "Inventario", icon: Boxes },
    { href: "/sales", label: "Ventas", icon: Receipt },
    { href: "/payments", label: "Pagos", icon: CreditCard },
    { href: "/billing", label: "Facturación", icon: FileText },
    { href: "/reports", label: "Reportes", icon: BarChart2 },
    { href: "/users", label: "Usuarios", icon: Users },
    { href: "/audit", label: "Auditoría", icon: ShieldCheck },
  ],
  supervisor: [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/products", label: "Productos", icon: Package },
    { href: "/inventory", label: "Inventario", icon: Boxes },
    { href: "/sales", label: "Ventas", icon: Receipt },
    { href: "/payments", label: "Pagos", icon: CreditCard },
    { href: "/billing", label: "Facturación", icon: FileText },
    { href: "/reports", label: "Reportes", icon: BarChart2 },
  ],
  cashier: [
    { href: "/pos", label: "Punto de Venta", icon: Monitor },
    { href: "/sales", label: "Mis Ventas", icon: Receipt },
  ],
};

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrador",
  supervisor: "Supervisor",
  cashier: "Cajero",
};

export function Sidebar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const role = useAuthStore((s) => s.role);

  const navItems = role ? NAV_ITEMS[role] : [];

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // proceed with logout even if request fails
    } finally {
      clearAuth();
      window.location.href = "/login";
    }
  }

  return (
    <aside className="w-60 shrink-0 bg-sidebar flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 h-14 border-b border-sidebar-border">
        <div className="w-7 h-7 rounded-md bg-sidebar-primary flex items-center justify-center shrink-0">
          <span className="text-white font-bold text-[13px] leading-none">S</span>
        </div>
        <span className="text-white font-semibold text-[15px] tracking-tight">SwiftSale</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        <ul className="space-y-0.5">
          {navItems.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href || pathname.startsWith(href + "/");
            return (
              <li key={href}>
                <Link
                  href={href}
                  className={[
                    "flex items-center gap-3 px-3 py-2 rounded-md text-[13.5px] font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                  ].join(" ")}
                >
                  <Icon
                    size={16}
                    className={isActive ? "text-sidebar-primary" : "opacity-70"}
                  />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User + Logout */}
      <div className="border-t border-sidebar-border px-4 py-3 space-y-2.5">
        <div className="space-y-0.5">
          <p className="text-sidebar-accent-foreground text-[13px] font-medium truncate">
            {user?.full_name ?? "—"}
          </p>
          <p className="text-sidebar-foreground text-[11px]">
            {role ? ROLE_LABELS[role] : ""}
          </p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-sidebar-foreground hover:text-destructive text-[13px] transition-colors w-full"
        >
          <LogOut size={14} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
