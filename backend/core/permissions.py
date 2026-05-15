from ninja.errors import HttpError

from apps.authentication.models import User


def require_admin(request) -> None:
    user: User = request.auth
    if user.role != User.Role.ADMIN:
        raise HttpError(403, "Admin access required")


def require_admin_or_supervisor(request) -> None:
    user: User = request.auth
    if user.role not in (User.Role.ADMIN, User.Role.SUPERVISOR):
        raise HttpError(403, "Insufficient permissions")
