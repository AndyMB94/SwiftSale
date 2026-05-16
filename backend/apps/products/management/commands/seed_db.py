"""
Seed the database with realistic convenience-store data (Tambo-style).

Usage:
    python manage.py seed_db              # seed categories + products
    python manage.py seed_db --flush      # delete everything first, then seed
"""

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.products.models import Category, Inventory, InventoryMovement, Product

User = get_user_model()

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        "slug": "bna",
        "name": "Bebidas No Alcohólicas",
        "description": "Gaseosas, aguas, jugos, energizantes y cafés.",
    },
    {
        "slug": "bal",
        "name": "Bebidas Alcohólicas",
        "description": "Cervezas, vinos, piscos y licores.",
    },
    {
        "slug": "snk",
        "name": "Snacks y Confitería",
        "description": "Chocolates, galletas, caramelos y snacks salados.",
    },
    {
        "slug": "com",
        "name": "Comidas Preparadas",
        "description": "Sándwiches, empanadas y alimentos listos para consumir.",
    },
    {
        "slug": "lac",
        "name": "Lácteos y Refrigerados",
        "description": "Yogures, leches, quesos y embutidos.",
    },
    {
        "slug": "hel",
        "name": "Congelados y Helados",
        "description": "Helados y alimentos congelados listos para calentar.",
    },
    {
        "slug": "per",
        "name": "Aseo Personal",
        "description": "Desodorantes, jabones, champús y artículos de higiene.",
    },
    {
        "slug": "aba",
        "name": "Abarrotes",
        "description": "Productos de primera necesidad: arroz, azúcar, conservas.",
    },
    {
        "slug": "lim",
        "name": "Limpieza y Hogar",
        "description": "Detergentes, papel higiénico y limpiadores.",
    },
    {
        "slug": "var",
        "name": "Varios y Accesorios",
        "description": "Pilas, encendedores, preservativos y accesorios de emergencia.",
    },
]

# (category_slug, name, price, low_stock_threshold, initial_qty)
PRODUCTS = [
    # ── Bebidas No Alcohólicas ───────────────────────────────────────────────
    ("bna", "Inca Kola 500 ml", "3.50", 10, 120),
    ("bna", "Coca-Cola 500 ml", "3.50", 10, 110),
    ("bna", "Sprite 500 ml", "3.50", 8, 95),
    ("bna", "Fanta Naranja 500 ml", "3.50", 8, 80),
    ("bna", "Agua San Luis 625 ml", "2.00", 15, 200),
    ("bna", "Agua Cielo 625 ml", "1.80", 15, 180),
    ("bna", "Powerade Mora Azul 500 ml", "4.00", 8, 70),
    ("bna", "Gatorade Naranja 500 ml", "4.50", 8, 65),
    ("bna", "Monster Energy 473 ml", "7.90", 6, 40),
    ("bna", "Red Bull 250 ml", "9.90", 6, 35),
    ("bna", "Frugos del Valle Durazno 300 ml", "3.00", 10, 90),
    ("bna", "Lipton Ice Tea Limón 500 ml", "3.50", 8, 60),
    ("bna", "Café Nescafé Lata 240 ml", "5.50", 6, 45),
    # ── Bebidas Alcohólicas ──────────────────────────────────────────────────
    ("bal", "Cristal Lata 355 ml", "5.50", 12, 150),
    ("bal", "Pilsen Callao Lata 355 ml", "5.50", 12, 140),
    ("bal", "Cusqueña Rubia 330 ml", "5.90", 10, 100),
    ("bal", "Heineken Lata 330 ml", "8.50", 8, 60),
    ("bal", "Corona Extra 355 ml", "8.90", 8, 55),
    ("bal", "Vino Clos Blanco 187 ml", "8.50", 6, 40),
    ("bal", "Pisco Tabernero Puro 200 ml", "18.00", 4, 25),
    ("bal", "Ron Cartavio Superior 250 ml", "15.00", 4, 30),
    # ── Snacks y Confitería ──────────────────────────────────────────────────
    ("snk", "Pringles Original 40 g", "6.50", 8, 60),
    ("snk", "Lays Clásicas 37 g", "3.50", 10, 90),
    ("snk", "Doritos Nacho Cheese 42 g", "4.00", 10, 85),
    ("snk", "Cheetos Flamin Hot 35 g", "3.50", 10, 80),
    ("snk", "Sublime 36 g", "2.50", 15, 120),
    ("snk", "Oreo Original 36 g", "2.00", 15, 130),
    ("snk", "Chokis Chips 52 g", "2.50", 12, 110),
    ("snk", "Casino Fresa 36 g", "2.00", 12, 100),
    ("snk", "M&Ms Maní 45 g", "5.50", 8, 55),
    ("snk", "Ambrosoli Surtido 90 g", "4.50", 8, 50),
    # ── Comidas Preparadas ───────────────────────────────────────────────────
    ("com", "Sándwich de Pollo", "8.50", 5, 20),
    ("com", "Empanada de Carne", "5.00", 5, 25),
    ("com", "Hamburguesa Simple", "12.00", 4, 15),
    ("com", "Hot Dog", "7.00", 4, 18),
    ("com", "Croissant Jamón y Queso", "8.00", 4, 12),
    # ── Lácteos y Refrigerados ───────────────────────────────────────────────
    ("lac", "Gloria Leche Entera UHT 1 L", "5.50", 10, 80),
    ("lac", "Yogur Gloria Frutado 165 g", "2.50", 12, 100),
    ("lac", "Yogur Laive Bebible 180 ml", "3.00", 10, 85),
    ("lac", "Queso Fresco Laive 250 g", "8.50", 6, 40),
    ("lac", "Mantequilla Gloria 100 g", "6.50", 6, 35),
    ("lac", "Leche Evaporada Gloria 400 g", "4.50", 8, 60),
    # ── Congelados y Helados ─────────────────────────────────────────────────
    ("hel", "Helado Magnum Clásico", "8.50", 6, 30),
    ("hel", "Helado Sublime D'Onofrio 65 ml", "3.50", 8, 45),
    ("hel", "Helado Motta Choco Donuts", "4.50", 6, 35),
    ("hel", "Helado Artika Vainilla Vaso 100 ml", "4.00", 6, 38),
    # ── Aseo Personal ────────────────────────────────────────────────────────
    ("per", "Rexona Roll-On Cotton 50 ml", "9.90", 6, 40),
    ("per", "Dove Jabón 90 g", "3.50", 8, 60),
    ("per", "Head & Shoulders Shampoo 90 ml", "6.50", 6, 45),
    ("per", "Oral-B Cepillo Dental Suave", "5.50", 6, 50),
    ("per", "Listerine Menta 95 ml", "7.00", 6, 40),
    ("per", "Kotex Toallas Nocturnas x3", "4.50", 6, 35),
    ("per", "Durex Natural x3", "12.00", 4, 25),
    # ── Abarrotes ────────────────────────────────────────────────────────────
    ("aba", "Azúcar Rubia 1 kg", "4.50", 8, 70),
    ("aba", "Arroz Costeño 1 kg", "4.00", 8, 65),
    ("aba", "Fideos Lavaggi Espagueti 250 g", "2.50", 10, 80),
    ("aba", "Atún Florida en Aceite 170 g", "4.50", 8, 60),
    ("aba", "Milo 170 g", "7.50", 6, 40),
    ("aba", "Café Altomayo Instantáneo 50 g", "5.00", 6, 45),
    # ── Limpieza y Hogar ─────────────────────────────────────────────────────
    ("lim", "Papel Higiénico Suave x4", "7.00", 8, 55),
    ("lim", "Detergente Ariel 500 g", "8.50", 6, 40),
    ("lim", "Limpiador Sapolio Multiusos 500 ml", "5.50", 6, 35),
    ("lim", "Lejía Clorox 500 ml", "4.50", 6, 40),
    # ── Varios y Accesorios ──────────────────────────────────────────────────
    ("var", "Pilas Panasonic AA x2", "4.50", 5, 30),
    ("var", "Encendedor BIC", "3.50", 6, 35),
    ("var", "Preservativo Tulipán x3", "9.50", 4, 20),
    ("var", "Bolsa de Hielo 1 kg", "4.00", 5, 25),
    ("var", "Cargador USB Genérico", "12.00", 3, 15),
]


def _sku(slug: str, index: int) -> str:
    return f"{slug.upper()}-{index:03d}"


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


class Command(BaseCommand):
    help = "Seed the database with categories, products and inventory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing categories, products and inventory before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write(self.style.WARNING("Flushing existing data..."))
            InventoryMovement.objects.all().delete()
            Inventory.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write("  Done.\n")

        # ── Categories ───────────────────────────────────────────────────────
        self.stdout.write("Creating categories...")
        cat_map: dict[str, Category] = {}
        for cat_data in CATEGORIES:
            slug = cat_data["slug"]
            cat, created = Category.objects.get_or_create(
                name=cat_data["name"],
                defaults={"description": cat_data["description"]},
            )
            cat_map[slug] = cat
            symbol = self.style.SUCCESS("  [+]") if created else "  [=]"
            self.stdout.write(f"{symbol} {cat.name}")

        # ── Products + Inventory ─────────────────────────────────────────────
        self.stdout.write("\nCreating products and inventory...")
        counters: dict[str, int] = {}
        created_count = 0
        skipped_count = 0

        for cat_slug, name, price, low_threshold, initial_qty in PRODUCTS:
            counters[cat_slug] = counters.get(cat_slug, 0) + 1
            sku = _sku(cat_slug, counters[cat_slug])

            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "category": cat_map[cat_slug],
                    "name": name,
                    "price": Decimal(price),
                    "is_active": True,
                },
            )

            if created:
                # Add some randomness to stock so the UI looks more realistic
                qty = initial_qty + random.randint(-5, 10)
                qty = max(0, qty)

                inv = Inventory.objects.create(
                    product=product,
                    quantity=qty,
                    low_stock_threshold=low_threshold,
                )
                InventoryMovement.objects.create(
                    inventory=inv,
                    movement_type=InventoryMovement.MovementType.PURCHASE,
                    quantity_delta=qty,
                    quantity_after=qty,
                    reason="Stock inicial (seed)",
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [+] {sku}  {name}  — qty: {qty}")
                )
            else:
                skipped_count += 1

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {created_count} products created, {skipped_count} already existed."
            )
        )

        # ── Admin user (convenience) ─────────────────────────────────────────
        if not User.objects.filter(role="admin").exists():
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("No admin user found. Creating one...")
            )
            User.objects.create_superuser(
                email="admin@swiftsale.pe",
                password="admin1234",
                full_name="Admin SwiftSale",
                role="admin",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "  [+] admin@swiftsale.pe / admin1234  ← change this in production!"
                )
            )
