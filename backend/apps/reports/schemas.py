from decimal import Decimal
from datetime import date
from ninja import Schema


class DailyRevenueRow(Schema):
    date: date
    revenue: Decimal
    sale_count: int
    avg_ticket: Decimal


class DailyRevenueOut(Schema):
    start: date
    end: date
    total_revenue: Decimal
    total_sales: int
    rows: list[DailyRevenueRow]


class BestSellerRow(Schema):
    product_id: int
    product_name: str
    sku: str
    total_quantity: int
    total_revenue: Decimal


class BestSellersOut(Schema):
    start: date
    end: date
    rows: list[BestSellerRow]


class InventoryValuationRow(Schema):
    product_id: int
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    valuation: Decimal


class InventoryValuationOut(Schema):
    total_valuation: Decimal
    rows: list[InventoryValuationRow]
