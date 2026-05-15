from .models import AuditLog


def log_action(
    action: str,
    target_type: str,
    target_id: str,
    actor=None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Fire-and-forget audit entry. Never raises — logging must not break requests.
    """
    try:
        AuditLog.objects.create(
            action=action,
            actor=actor,
            target_type=target_type,
            target_id=str(target_id),
            metadata=metadata or {},
            ip_address=ip_address,
        )
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Failed to write audit log: action=%s target=%s/%s",
            action,
            target_type,
            target_id,
        )
