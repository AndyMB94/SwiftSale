import pytest
from decimal import Decimal
from datetime import date, timedelta

from apps.authentication.models import User
from apps.products.models import Category, Product, Inventory
from apps.sales.services import SaleService
from apps.reports.services import ReportService


@pytest.fixture
def cashier(db):
    return User.objects.create_user(
        email='reports_cashier@test.com',
        password='testpass123',
        full_name='Reports Cashier',
        role=User.Role.CASHIER,
    )


@pytest.fixture
def setup_products(db):
    cat = Category.objects.create(name='Bebidas Rep')
    p1 = Product.objects.create(category=cat, name='Coca Cola', sku='CC-R', price=Decimal('5.00'))
    p2 = Product.objects.create(category=cat, name='Pepsi', sku='PP-R', price=Decimal('4.00'))
    Inventory.objects.create(product=p1, quantity=100)
    Inventory.objects.create(product=p2, quantity=100)
    return p1, p2


# ── Daily Revenue ─────────────────────────────────────────────────────────────

class TestDailyRevenue:
    def test_returns_revenue_for_completed_sales(self, db, cashier, setup_products):
        p1, _ = setup_products
        SaleService.create_sale(cashier=cashier, items=[{'product_id': p1.id, 'quantity': 2}])

        today = date.today()
        result = ReportService.daily_revenue(today, today)

        assert result['total_sales'] == 1
        assert result['total_revenue'] > Decimal('0')
        assert len(result['rows']) == 1
        assert result['rows'][0]['date'] == today

    def test_excludes_cancelled_sales(self, db, cashier, setup_products):
        p1, _ = setup_products
        sale = SaleService.create_sale(cashier=cashier, items=[{'product_id': p1.id, 'quantity': 1}])
        SaleService.cancel_sale(sale_id=sale.id, cancelled_by=cashier)

        today = date.today()
        result = ReportService.daily_revenue(today, today)

        assert result['total_sales'] == 0
        assert result['total_revenue'] == Decimal('0')

    def test_empty_range_returns_zero(self, db):
        yesterday = date.today() - timedelta(days=1)
        result = ReportService.daily_revenue(yesterday, yesterday)

        assert result['total_sales'] == 0
        assert result['total_revenue'] == Decimal('0')
        assert result['rows'] == []

    def test_avg_ticket_calculated_correctly(self, db, cashier, setup_products):
        p1, _ = setup_products
        SaleService.create_sale(cashier=cashier, items=[{'product_id': p1.id, 'quantity': 2}])

        today = date.today()
        result = ReportService.daily_revenue(today, today)

        row = result['rows'][0]
        assert row['avg_ticket'] == row['revenue']  # 1 sale, avg == total

    def test_multiple_sales_aggregated_per_day(self, db, cashier, setup_products):
        p1, p2 = setup_products
        SaleService.create_sale(cashier=cashier, items=[{'product_id': p1.id, 'quantity': 1}])
        SaleService.create_sale(cashier=cashier, items=[{'product_id': p2.id, 'quantity': 1}])

        today = date.today()
        result = ReportService.daily_revenue(today, today)

        assert result['total_sales'] == 2
        assert len(result['rows']) == 1  # same day, one row


# ── Best Sellers ──────────────────────────────────────────────────────────────

class TestBestSellers:
    def test_returns_products_sorted_by_quantity(self, db, cashier, setup_products):
        p1, p2 = setup_products
        SaleService.create_sale(cashier=cashier, items=[{'product_id': p1.id, 'quantity': 5}])
        SaleService.create_sale(cashier=cashier, items=[{'product_id': p2.id, 'quantity': 2}])

        today = date.today()
        result = ReportService.best_sellers(today, today)

        assert len(result['rows']) == 2
        assert result['rows'][0]['sku'] == 'CC-R'  # highest quantity
        assert result['rows'][0]['total_quantity'] == 5
        assert result['rows'][1]['sku'] == 'PP-R'

    def test_empty_range_returns_empty(self, db):
        yesterday = date.today() - timedelta(days=1)
        result = ReportService.best_sellers(yesterday, yesterday)
        assert result['rows'] == []

    def test_limit_respected(self, db, cashier, setup_products):
        p1, p2 = setup_products
        SaleService.create_sale(cashier=cashier, items=[
            {'product_id': p1.id, 'quantity': 3},
            {'product_id': p2.id, 'quantity': 2},
        ])

        today = date.today()
        result = ReportService.best_sellers(today, today, limit=1)
        assert len(result['rows']) == 1

    def test_excludes_cancelled_sales(self, db, cashier, setup_products):
        p1, _ = setup_products
        sale = SaleService.create_sale(cashier=cashier, items=[{'product_id': p1.id, 'quantity': 10}])
        SaleService.cancel_sale(sale_id=sale.id, cancelled_by=cashier)

        today = date.today()
        result = ReportService.best_sellers(today, today)
        assert result['rows'] == []


# ── Inventory Valuation ───────────────────────────────────────────────────────

class TestInventoryValuation:
    def test_calculates_valuation_per_product(self, db, setup_products):
        p1, p2 = setup_products
        # p1: 100 units * 5.00 = 500, p2: 100 units * 4.00 = 400

        result = ReportService.inventory_valuation()

        skus = {r['sku']: r for r in result['rows']}
        assert skus['CC-R']['valuation'] == Decimal('500.00')
        assert skus['PP-R']['valuation'] == Decimal('400.00')
        assert result['total_valuation'] == Decimal('900.00')

    def test_excludes_inactive_products(self, db, setup_products):
        p1, _ = setup_products
        p1.is_active = False
        p1.save()

        result = ReportService.inventory_valuation()
        skus = [r['sku'] for r in result['rows']]
        assert 'CC-R' not in skus

    def test_empty_inventory_returns_zero_total(self, db):
        result = ReportService.inventory_valuation()
        assert result['total_valuation'] == Decimal('0')
        assert result['rows'] == []
