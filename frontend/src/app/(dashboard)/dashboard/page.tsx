import type { Metadata } from "next";

export const metadata: Metadata = { title: "Dashboard — SwiftSale" };

export default function DashboardPage() {
  return (
    <div className="space-y-1">
      <h2 className="text-2xl font-bold tracking-tight">Bienvenido</h2>
      <p className="text-muted-foreground text-sm">
        El dashboard estará disponible en Phase F2.
      </p>
    </div>
  );
}
