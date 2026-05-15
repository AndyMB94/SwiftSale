import uuid

from django.db import models


class Payment(models.Model):
    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        YAPE = "yape", "Yape"
        PLIN = "plin", "Plin"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(
        "sales.Sale", on_delete=models.PROTECT, related_name="payments"
    )
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    # Set by provider webhook — used for duplicate webhook detection
    provider_ref = models.CharField(max_length=255, null=True, blank=True, unique=True)
    # Client-generated key — prevents duplicate payment processing
    idempotency_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sale"]),
            models.Index(fields=["status"]),
            models.Index(fields=["provider_ref"]),
        ]

    def __str__(self):
        return f"Payment {self.id} — {self.method} {self.status}"
