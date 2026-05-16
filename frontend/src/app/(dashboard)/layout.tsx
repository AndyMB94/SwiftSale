"use client";

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { useAuthStore } from "@/store/authStore";
import { useAuthInit } from "@/hooks/useAuth";
import { useWebSocket, type WsMessage } from "@/hooks/useWebSocket";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useAuthInit();

  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const role = useAuthStore((s) => s.role);

  const handleWsMessage = useCallback(
    (msg: WsMessage) => {
      if (msg.event === "inventory.low_stock") {
        toast.warning(
          `Stock bajo: ${msg.product_name} (${msg.current_quantity} uds.)`,
          { duration: 8000 },
        );
      }
    },
    [],
  );

  useWebSocket({
    onMessage: handleWsMessage,
    enabled: isAuthenticated && (role === "admin" || role === "supervisor"),
  });

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.push("/login");
    } else if (role === "cashier") {
      router.push("/pos");
    }
  }, [isLoading, isAuthenticated, role, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground text-sm">Cargando...</div>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
