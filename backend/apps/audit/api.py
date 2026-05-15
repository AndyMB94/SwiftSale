from datetime import date

from ninja import Router
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.authentication.security import CookieJWTAuth

from .models import AuditLog
from .schemas import AuditLogOut

router = Router(tags=["audit"])
auth = CookieJWTAuth()


def _require_admin(request):
    if request.auth.role != User.Role.ADMIN:
        raise HttpError(403, "Admin access required")


@router.get("", response=list[AuditLogOut], auth=auth)
def list_audit_logs(
    request,
    action: str | None = None,
    actor_id: str | None = None,
    target_type: str | None = None,
    start: date | None = None,
    end: date | None = None,
    limit: int = 100,
):
    _require_admin(request)

    qs = AuditLog.objects.select_related("actor").order_by("-created_at")

    if action:
        qs = qs.filter(action=action)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)
    if target_type:
        qs = qs.filter(target_type=target_type)
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)

    limit = min(limit, 500)
    return list(qs[:limit])
