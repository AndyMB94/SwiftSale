"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { UserPlus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listUsers, createUser, updateUser } from "@/services/users";
import { formatDateTime } from "@/utils/formatters";
import { usePageTitle } from "@/hooks/usePageTitle";
import type { AppUser, UserRole } from "@/types/users";

const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Admin",
  supervisor: "Supervisor",
  cashier: "Cajero",
};

const ROLE_VARIANTS: Record<
  UserRole,
  "default" | "secondary" | "outline"
> = {
  admin: "default",
  supervisor: "secondary",
  cashier: "outline",
};

interface CreateForm {
  email: string;
  full_name: string;
  role: UserRole;
  password: string;
}

const EMPTY_FORM: CreateForm = {
  email: "",
  full_name: "",
  role: "cashier",
  password: "",
};

export default function UsersPage() {
  usePageTitle("Usuarios");

  const qc = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState<CreateForm>(EMPTY_FORM);
  const [deactivateTarget, setDeactivateTarget] = useState<AppUser | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: listUsers,
  });

  const users = data?.data.results ?? [];

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      toast.success("Usuario creado");
      qc.invalidateQueries({ queryKey: ["users"] });
      setCreateOpen(false);
      setForm(EMPTY_FORM);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(detail ?? "Error al crear usuario");
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (user: AppUser) =>
      updateUser(user.id, { is_active: !user.is_active }),
    onSuccess: (_, user) => {
      toast.success(user.is_active ? "Usuario reactivado" : "Usuario desactivado");
      qc.invalidateQueries({ queryKey: ["users"] });
      setDeactivateTarget(null);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      toast.error(detail ?? "Error al actualizar usuario");
    },
  });

  const canSubmit =
    form.email.trim() &&
    form.full_name.trim() &&
    form.password.length >= 8 &&
    !createMutation.isPending;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Usuarios</h1>
        <Button onClick={() => setCreateOpen(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Nuevo usuario
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead className="text-center">Estado</TableHead>
              <TableHead>Creado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-muted-foreground py-10"
                >
                  No hay usuarios registrados
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <TableRow key={user.id} className={!user.is_active ? "opacity-50" : ""}>
                  <TableCell className="font-medium">{user.full_name}</TableCell>
                  <TableCell className="text-muted-foreground">{user.email}</TableCell>
                  <TableCell>
                    <Badge variant={ROLE_VARIANTS[user.role as UserRole] ?? "outline"}>
                      {ROLE_LABELS[user.role as UserRole] ?? user.role}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={user.is_active ? "default" : "outline"}>
                      {user.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatDateTime(user.created_at)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant={user.is_active ? "destructive" : "outline"}
                      onClick={() => setDeactivateTarget(user)}
                      disabled={deactivateMutation.isPending}
                    >
                      {user.is_active ? "Desactivar" : "Reactivar"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create user dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent aria-describedby={undefined} className="max-w-md">
          <DialogHeader>
            <DialogTitle>Nuevo usuario</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            <div className="space-y-1">
              <Label>Nombre completo</Label>
              <Input
                value={form.full_name}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
                placeholder="Ej: Juan Pérez"
              />
            </div>
            <div className="space-y-1">
              <Label>Email</Label>
              <Input
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="usuario@empresa.com"
              />
            </div>
            <div className="space-y-1">
              <Label>Rol</Label>
              <Select
                value={form.role}
                onValueChange={(v) => setForm((f) => ({ ...f, role: v as UserRole }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cashier">Cajero</SelectItem>
                  <SelectItem value="supervisor">Supervisor</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label>Contraseña</Label>
              <Input
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="Mínimo 8 caracteres"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancelar
            </Button>
            <Button
              disabled={!canSubmit}
              onClick={() => createMutation.mutate(form)}
            >
              {createMutation.isPending ? "Creando..." : "Crear usuario"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Deactivate confirmation dialog */}
      <Dialog
        open={!!deactivateTarget}
        onOpenChange={(o) => !o && setDeactivateTarget(null)}
      >
        <DialogContent aria-describedby={undefined} className="max-w-sm">
          <DialogHeader>
            <DialogTitle>
              {deactivateTarget?.is_active ? "Desactivar usuario" : "Reactivar usuario"}
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            {deactivateTarget?.is_active
              ? `¿Desactivar a ${deactivateTarget?.full_name}? No podrá iniciar sesión.`
              : `¿Reactivar a ${deactivateTarget?.full_name}?`}
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeactivateTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant={deactivateTarget?.is_active ? "destructive" : "default"}
              disabled={deactivateMutation.isPending}
              onClick={() => deactivateTarget && deactivateMutation.mutate(deactivateTarget)}
            >
              {deactivateMutation.isPending
                ? "Procesando..."
                : deactivateTarget?.is_active
                ? "Desactivar"
                : "Reactivar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
