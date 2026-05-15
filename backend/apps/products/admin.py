from django.contrib import admin

from .models import Category, Inventory, InventoryMovement, Product

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(InventoryMovement)
