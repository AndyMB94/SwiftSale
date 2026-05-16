export const IGV_RATE = 0.18;

export const PAYMENT_METHODS = [
  { value: "cash", label: "Efectivo" },
  { value: "card", label: "Tarjeta" },
  { value: "yape", label: "Yape" },
  { value: "plin", label: "Plin" },
] as const;

export const SALE_STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  completed: "Completado",
  cancelled: "Cancelado",
};

export const PAYMENT_STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  paid: "Pagado",
  failed: "Fallido",
  refunded: "Devuelto",
};

export const ADJUSTMENT_REASONS = [
  { value: "purchase", label: "Compra" },
  { value: "return", label: "Devolución" },
  { value: "damaged_goods", label: "Mercadería dañada" },
  { value: "correction", label: "Corrección" },
] as const;

export const BILLING_STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  sent: "Enviado",
  accepted: "Aceptado",
  rejected: "Rechazado",
  voided: "Anulado",
};

export const WS_RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000];
