import uuid

from django.db import models


class BillingSeries(models.Model):
    class DocumentType(models.TextChoices):
        BOLETA = 'boleta', 'Boleta de Venta'
        FACTURA = 'factura', 'Factura Electrónica'

    series = models.CharField(max_length=4, unique=True)
    document_type = models.CharField(max_length=10, choices=DocumentType.choices)
    last_correlativo = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_series'
        verbose_name_plural = 'billing series'

    def __str__(self):
        return f'{self.series} (last: {self.last_correlativo})'


class BillingDocument(models.Model):
    class DocumentType(models.TextChoices):
        BOLETA = 'boleta', 'Boleta de Venta'
        FACTURA = 'factura', 'Factura Electrónica'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SENT = 'sent', 'Sent to OSE'
        ACCEPTED = 'accepted', 'Accepted by SUNAT'
        REJECTED = 'rejected', 'Rejected by SUNAT'
        VOIDED = 'voided', 'Voided (Baja)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    series = models.ForeignKey(
        BillingSeries, on_delete=models.PROTECT, related_name='documents'
    )
    correlativo = models.IntegerField()
    full_number = models.CharField(max_length=20, unique=True)
    document_type = models.CharField(max_length=10, choices=DocumentType.choices)
    sale = models.ForeignKey(
        'sales.Sale', on_delete=models.PROTECT, related_name='billing_documents'
    )
    customer_name = models.CharField(max_length=255)
    customer_document_type = models.CharField(max_length=10)
    customer_document_number = models.CharField(max_length=20)
    customer_address = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    xml_content = models.TextField()
    sunat_cdr = models.TextField(blank=True)
    sunat_response_code = models.CharField(max_length=10, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    voided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'billing_documents'
        indexes = [
            models.Index(fields=['full_number']),
            models.Index(fields=['sale']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.full_number} — {self.status}'
