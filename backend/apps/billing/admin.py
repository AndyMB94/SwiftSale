from django.contrib import admin
from .models import BillingSeries, BillingDocument

admin.site.register(BillingSeries)
admin.site.register(BillingDocument)
