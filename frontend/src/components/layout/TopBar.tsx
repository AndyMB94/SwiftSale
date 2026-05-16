"use client";

import { usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/products": "Productos",
  "/inventory": "Inventario",
  "/sales": "Ventas",
  "/payments": "Pagos",
  "/billing": "Facturación",
  "/reports": "Reportes",
  "/users": "Usuarios",
  "/audit": "Auditoría",
};

export function TopBar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);

  const segment = "/" + (pathname.split("/")[1] ?? "");
  const title = PAGE_TITLES[segment] ?? "SwiftSale";

  return (
    <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6 shrink-0">
      <h1 className="text-[15px] font-semibold text-foreground">{title}</h1>
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="text-primary text-[12px] font-semibold">
            {user?.full_name?.charAt(0).toUpperCase() ?? "?"}
          </span>
        </div>
        <span className="text-sm text-muted-foreground hidden sm:block">
          {user?.full_name}
        </span>
      </div>
    </header>
  );
}
