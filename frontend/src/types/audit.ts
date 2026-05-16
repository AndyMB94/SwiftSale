export interface AuditLog {
  id: string;
  action: string;
  actor_id: string | null;
  target_type: string;
  target_id: string;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}
