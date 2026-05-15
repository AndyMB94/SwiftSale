from datetime import datetime
from uuid import UUID

from ninja import Schema


class AuditLogOut(Schema):
    id: UUID
    action: str
    actor_id: UUID | None
    target_type: str
    target_id: str
    metadata: dict
    ip_address: str | None
    created_at: datetime
