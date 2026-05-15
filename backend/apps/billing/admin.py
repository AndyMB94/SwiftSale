from django.contrib import admin

from .models import BillingDocument, BillingSeries

admin.site.register(BillingSeries)
admin.site.register(BillingDocument)
