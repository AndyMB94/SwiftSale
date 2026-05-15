import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    class Action(models.TextChoices):
        PRICE_CHANGE = 'price_change', 'Price Change'
        STOCK_EDIT = 'stock_edit', 'Stock Edit'
        SALE_CANCELLED = 'sale_cancelled', 'Sale Cancelled'
        LOGIN_FAILED = 'login_failed', 'Login Failed'
        USER_DEACTIVATED = 'user_deactivated', 'User Deactivated'
        DOCUMENT_VOIDED = 'document_voided', 'Document Voided'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
    )
    target_type = models.CharField(max_length=50)
    target_id = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f'{self.action} by {self.actor_id} at {self.created_at}'
