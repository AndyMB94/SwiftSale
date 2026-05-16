import api from "./api";
import type { AuditLog } from "@/types/audit";

export const getAuditLogs = (params: {
  action?: string;
  actor_id?: string;
  target_type?: string;
  start?: string;
  end?: string;
  limit?: number;
}) => api.get<AuditLog[]>("/api/v1/audit", { params });
