"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ChevronLeft, ChevronRight, Eye, FileText, X, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  getBillingDocuments,
  getBillingSeries,
  issueBoleta,
  issueFactura,
  voidDocument,
} from "@/services/billing";
import { getSale } from "@/services/sales";
import { formatCurrency, formatDateTime } from "@/utils/formatters";
import { useAuthStore } from "@/store/authStore";
import type { BillingDocument, CustomerDocumentType } from "@/types/billing";
import type { Sale } from "@/types/sales";

const PAGE_SIZE = 20;

const TYPE_LABELS: Record<string, string> = {
  boleta: "Boleta",
  factura: "Factura",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendiente",
  sent: "Enviado",
  accepted: "Aceptado",
  rejected: "Rechazado",
  voided: "Anulado",
};

const STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  accepted: "default",
  sent: "secondary",
  pending: "secondary",
  rejected: "destructive",
  voided: "outline",
};

type ModalType = "boleta" | "factura" | null;

interface IssueForm {
  saleId: string;
  series: string;
  customerName: string;
  customerDocType: CustomerDocumentType;
  customerDocNumber: string;
  customerAddress: string;
}

const EMPTY_FORM: IssueForm = {
  saleId: "",
  series: "",
  customerName: "",
  customerDocType: "DNI",
  customerDocNumber: "",
  customerAddress: "",
};

export default function BillingPage() {
  const qc = useQueryClient();
  const role = useAuthStore((s) => s.role);
  const searchParams = useSearchParams();

  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [saleIdFilter, setSaleIdFilter] = useState(
    () => searchParams.get("sale_id") ?? "",
  );
  const [page, setPage] = useState(1);

  const [modalType, setModalType] = useState<ModalType>(null);
  const [form, setForm] = useState<IssueForm>(EMPTY_FORM);
  const [fetchedSale, setFetchedSale] = useState<Sale | null>(null);
  const [fetchingSale, setFetchingSale] = useState(false);

  const [selectedDoc, setSelectedDoc] = useState<BillingDocument | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [voidReason, setVoidReason] = useState("");
  const [voidConfirm, setVoidConfirm] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [typeFilter, statusFilter, saleIdFilter]);

  const { data, isLoading } = useQuery({
    queryKey: ["billing", { typeFilter, statusFilter, saleIdFilter, page }],
    queryFn: () =>
      getBillingDocuments({
        document_type: typeFilter === "all" ? undefined : typeFilter,
        status: statusFilter === "all" ? undefined : statusFilter,
        sale_id: saleIdFilter || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
  });

  const { data: seriesData } = useQuery({
    queryKey: ["billing-series"],
    queryFn: getBillingSeries,
  });

  const availableSeries = seriesData?.data ?? [];
  const filteredSeries = availableSeries.filter(
    (s) => s.document_type === modalType,
  );

  async function fetchSale() {
    if (!form.saleId.trim()) return;
    setFetchingSale(true);
    try {
      const res = await getSale(form.saleId.trim());
      setFetchedSale(res.data);
    } catch {
      toast.error("Venta no encontrada");
      setFetchedSale(null);
    } finally {
      setFetchingSale(false);
    }
  }

  const issueMutation = useMutation({
    mutationFn: async () => {
      if (!fetchedSale) throw new Error("No sale loaded");
      const items = fetchedSale.items.map((i) => ({
        product_id: i.product_id,
        quantity: i.quantity,
        unit_price: i.unit_price,
        description: i.product_name,
      }));
      if (modalType === "boleta") {
        return issueBoleta({
          sale_id: fetchedSale.id,
          series: form.series,
          customer_name: form.customerName,
          customer_document_type: form.customerDocType,
          customer_document_number: form.customerDocNumber,
          items,
        });
      } else {
        return issueFactura({
          sale_id: fetchedSale.id,
          series: form.series,
          customer_name: form.customerName,
          customer_document_number: form.customerDocNumber,
          customer_address: form.customerAddress,
          items,
        });
      }
    },
    onSuccess: () => {
      toast.success(
        modalType === "boleta" ? "Boleta emitida" : "Factura emitida",
      );
      qc.invalidateQueries({ queryKey: ["billing"] });
      setModalType(null);
      setForm(EMPTY_FORM);
      setFetchedSale(null);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(detail ?? "Error al emitir el comprobante");
    },
  });

  const voidMutation = useMutation({
    mutationFn: () => voidDocument(selectedDoc!.id, voidReason),
    onSuccess: () => {
      toast.success("Documento anulado");
      qc.invalidateQueries({ queryKey: ["billing"] });
      setVoidConfirm(false);
      setVoidReason("");
      setSheetOpen(false);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(detail ?? "Error al anular el documento");
    },
  });

  const docs = data?.data;
  const from = docs ? (docs.page - 1) * docs.page_size + 1 : 0;
  const to = docs ? Math.min(docs.page * docs.page_size, docs.count) : 0;

  function openModal(type: ModalType) {
    setModalType(type);
    setForm({ ...EMPTY_FORM, series: filteredSeries[0]?.series ?? "" });
    setFetchedSale(null);
  }

  function openDetail(doc: BillingDocument) {
    setSelectedDoc(doc);
    setVoidConfirm(false);
    setVoidReason("");
    setSheetOpen(true);
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Facturación</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => openModal("boleta")}>
            <FileText className="h-4 w-4 mr-2" />
            Emitir boleta
          </Button>
          <Button onClick={() => openModal("factura")}>
            <FileText className="h-4 w-4 mr-2" />
            Emitir factura
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-end">
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Tipo</Label>
          <Select value={typeFilter} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="boleta">Boleta</SelectItem>
              <SelectItem value="factura">Factura</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-muted-foreground">Estado</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="accepted">Aceptado</SelectItem>
              <SelectItem value="pending">Pendiente</SelectItem>
              <SelectItem value="rejected">Rechazado</SelectItem>
              <SelectItem value="voided">Anulado</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {saleIdFilter && (
          <div className="flex items-center gap-1.5 text-sm bg-muted px-3 py-1.5 rounded-md">
            <span className="text-muted-foreground">Venta:</span>
            <span className="font-mono text-xs">{saleIdFilter.slice(0, 8)}…</span>
            <button
              onClick={() => setSaleIdFilter("")}
              className="ml-1 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Número</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Cliente</TableHead>
              <TableHead>Doc.</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-center">Estado SUNAT</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !docs || docs.results.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="text-center text-muted-foreground py-10"
                >
                  {typeFilter !== "all" || statusFilter !== "all"
                    ? "Sin resultados para los filtros aplicados"
                    : "No hay comprobantes emitidos"}
                </TableCell>
              </TableRow>
            ) : (
              docs.results.map((doc: BillingDocument) => (
                <TableRow key={doc.id}>
                  <TableCell className="font-mono text-sm">
                    {doc.full_number}
                  </TableCell>
                  <TableCell>
                    {TYPE_LABELS[doc.document_type] ?? doc.document_type}
                  </TableCell>
                  <TableCell className="max-w-40 truncate">
                    {doc.customer_name}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {doc.customer_document_number}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(doc.total)}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={STATUS_VARIANTS[doc.status] ?? "outline"}>
                      {STATUS_LABELS[doc.status] ?? doc.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDateTime(doc.issued_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openDetail(doc)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        {docs && docs.count > 0 && (
          <div className="flex items-center justify-between px-4 py-3 border-t text-sm text-muted-foreground">
            <span>
              Mostrando {from}–{to} de {docs.count} comprobantes
            </span>
            <div className="flex gap-1">
              <Button
                size="icon"
                variant="ghost"
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                disabled={page === docs.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Issue modal (boleta / factura) */}
      <Dialog open={!!modalType} onOpenChange={(o) => !o && setModalType(null)}>
        <DialogContent aria-describedby={undefined} className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {modalType === "boleta" ? "Emitir Boleta" : "Emitir Factura"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Sale lookup */}
            <div className="space-y-1">
              <Label>ID de venta</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="UUID de la venta"
                  value={form.saleId}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, saleId: e.target.value }))
                  }
                />
                <Button
                  variant="outline"
                  onClick={fetchSale}
                  disabled={fetchingSale}
                >
                  Buscar
                </Button>
              </div>
              {fetchedSale && (
                <p className="text-xs text-muted-foreground">
                  Venta encontrada · {fetchedSale.items.length} productos ·{" "}
                  {formatCurrency(fetchedSale.total)}
                </p>
              )}
            </div>

            {/* Series */}
            <div className="space-y-1">
              <Label>Serie</Label>
              {filteredSeries.length > 0 ? (
                <Select
                  value={form.series}
                  onValueChange={(v) => setForm((f) => ({ ...f, series: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar serie" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredSeries.map((s) => (
                      <SelectItem key={s.id} value={s.series}>
                        {s.series}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Input
                  placeholder={modalType === "boleta" ? "B001" : "F001"}
                  value={form.series}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, series: e.target.value }))
                  }
                />
              )}
            </div>

            <Separator />

            {/* Customer info */}
            <div className="space-y-3">
              <p className="text-sm font-medium">Datos del cliente</p>

              <div className="space-y-1">
                <Label>Nombre / Razón social</Label>
                <Input
                  value={form.customerName}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, customerName: e.target.value }))
                  }
                />
              </div>

              {modalType === "boleta" ? (
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label>Tipo de documento</Label>
                    <Select
                      value={form.customerDocType}
                      onValueChange={(v) =>
                        setForm((f) => ({
                          ...f,
                          customerDocType: v as CustomerDocumentType,
                        }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="DNI">DNI</SelectItem>
                        <SelectItem value="CE">CE</SelectItem>
                        <SelectItem value="PASAPORTE">Pasaporte</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label>Número</Label>
                    <Input
                      value={form.customerDocNumber}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          customerDocNumber: e.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
              ) : (
                <>
                  <div className="space-y-1">
                    <Label>RUC</Label>
                    <Input
                      placeholder="11 dígitos"
                      value={form.customerDocNumber}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          customerDocNumber: e.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label>Dirección fiscal</Label>
                    <Input
                      value={form.customerAddress}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          customerAddress: e.target.value,
                        }))
                      }
                    />
                  </div>
                </>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setModalType(null)}>
              Cancelar
            </Button>
            <Button
              disabled={
                !fetchedSale ||
                !form.series ||
                !form.customerName ||
                !form.customerDocNumber ||
                issueMutation.isPending
              }
              onClick={() => issueMutation.mutate()}
            >
              {issueMutation.isPending ? "Emitiendo..." : "Emitir"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Document detail slide-over */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent
          className="w-full sm:max-w-lg overflow-y-auto"
          aria-describedby={undefined}
        >
          <SheetHeader>
            <SheetTitle>Detalle del comprobante</SheetTitle>
          </SheetHeader>

          {selectedDoc && (
            <div className="px-4 pb-6 space-y-6">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Número</p>
                  <p className="font-mono font-medium">
                    {selectedDoc.full_number}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Estado</p>
                  <Badge variant={STATUS_VARIANTS[selectedDoc.status] ?? "outline"}>
                    {STATUS_LABELS[selectedDoc.status] ?? selectedDoc.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-muted-foreground">Tipo</p>
                  <p className="font-medium">
                    {TYPE_LABELS[selectedDoc.document_type]}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Fecha</p>
                  <p className="font-medium">
                    {formatDateTime(selectedDoc.issued_at)}
                  </p>
                </div>
              </div>

              <Separator />

              <div className="space-y-1 text-sm">
                <p className="font-semibold mb-2">Cliente</p>
                <p>{selectedDoc.customer_name}</p>
                <p className="text-muted-foreground">
                  {selectedDoc.customer_document_type}:{" "}
                  {selectedDoc.customer_document_number}
                </p>
              </div>

              <Separator />

              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>{formatCurrency(selectedDoc.subtotal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">IGV (18%)</span>
                  <span>{formatCurrency(selectedDoc.tax)}</span>
                </div>
                <div className="flex justify-between font-bold text-base pt-1">
                  <span>Total</span>
                  <span>{formatCurrency(selectedDoc.total)}</span>
                </div>
              </div>

              {selectedDoc.sunat_response_code && (
                <>
                  <Separator />
                  <div className="text-sm">
                    <p className="text-muted-foreground mb-1">
                      Código respuesta SUNAT
                    </p>
                    <p className="font-mono">{selectedDoc.sunat_response_code}</p>
                  </div>
                </>
              )}

              {selectedDoc.voided_at && (
                <>
                  <Separator />
                  <div className="text-sm">
                    <p className="text-muted-foreground">Anulado el</p>
                    <p>{formatDateTime(selectedDoc.voided_at)}</p>
                  </div>
                </>
              )}

              {/* Void action — admin only, accepted documents */}
              {role === "admin" && selectedDoc.status === "accepted" && (
                <>
                  <Separator />
                  {!voidConfirm ? (
                    <Button
                      variant="destructive"
                      className="w-full"
                      onClick={() => setVoidConfirm(true)}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Anular documento
                    </Button>
                  ) : (
                    <div className="space-y-3">
                      <div className="space-y-1">
                        <Label>Motivo de anulación</Label>
                        <Input
                          value={voidReason}
                          onChange={(e) => setVoidReason(e.target.value)}
                          placeholder="Ej: Error en datos del cliente"
                        />
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          className="flex-1"
                          onClick={() => setVoidConfirm(false)}
                        >
                          Cancelar
                        </Button>
                        <Button
                          variant="destructive"
                          className="flex-1"
                          disabled={!voidReason.trim() || voidMutation.isPending}
                          onClick={() => voidMutation.mutate()}
                        >
                          Confirmar anulación
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
