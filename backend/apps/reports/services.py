from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate

from apps.products.models import Inventory
from apps.sales.models import Sale, SaleItem


class ReportService:
    @staticmethod
    def daily_revenue(start: date, end: date) -> dict:
        rows = (
            Sale.objects.filter(
                status=Sale.Status.COMPLETED,
                created_at__date__gte=start,
                created_at__date__lte=end,
            )
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                revenue=Sum("total"),
                sale_count=Count("id"),
            )
            .order_by("day")
        )

        result_rows = []
        total_revenue = Decimal("0")
        total_sales = 0

        for row in rows:
            revenue = row["revenue"] or Decimal("0")
            count = row["sale_count"]
            avg = (revenue / count).quantize(Decimal("0.01")) if count else Decimal("0")
            result_rows.append(
                {
                    "date": row["day"],
                    "revenue": revenue,
                    "sale_count": count,
                    "avg_ticket": avg,
                }
            )
            total_revenue += revenue
            total_sales += count

        return {
            "start": start,
            "end": end,
            "total_revenue": total_revenue,
            "total_sales": total_sales,
            "rows": result_rows,
        }

    @staticmethod
    def best_sellers(start: date, end: date, limit: int = 10) -> dict:
        rows = (
            SaleItem.objects.filter(
                sale__status=Sale.Status.COMPLETED,
                sale__created_at__date__gte=start,
                sale__created_at__date__lte=end,
            )
            .values("product_id", "product__name", "product__sku")
            .annotate(
                total_quantity=Sum("quantity"),
                total_revenue=Sum("subtotal"),
            )
            .order_by("-total_quantity")[:limit]
        )

        return {
            "start": start,
            "end": end,
            "rows": [
                {
                    "product_id": r["product_id"],
                    "product_name": r["product__name"],
                    "sku": r["product__sku"],
                    "total_quantity": r["total_quantity"],
                    "total_revenue": r["total_revenue"] or Decimal("0"),
                }
                for r in rows
            ],
        }

    @staticmethod
    def inventory_valuation() -> dict:
        rows = (
            Inventory.objects.select_related("product")
            .filter(product__is_active=True)
            .annotate(
                valuation=ExpressionWrapper(
                    F("quantity") * F("product__price"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
            .order_by("-valuation")
        )

        result_rows = []
        total = Decimal("0")

        for inv in rows:
            val = inv.valuation or Decimal("0")
            result_rows.append(
                {
                    "product_id": inv.product_id,
                    "product_name": inv.product.name,
                    "sku": inv.product.sku,
                    "quantity": inv.quantity,
                    "unit_price": inv.product.price,
                    "valuation": val,
                }
            )
            total += val

        return {
            "total_valuation": total,
            "rows": result_rows,
        }
