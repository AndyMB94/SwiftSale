from datetime import date

from ninja import Router
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.authentication.security import CookieJWTAuth

from .schemas import BestSellersOut, DailyRevenueOut, InventoryValuationOut
from .services import ReportService

router = Router(tags=['reports'])
auth = CookieJWTAuth()


def _require_supervisor_or_above(request):
    if request.auth.role not in (User.Role.SUPERVISOR, User.Role.ADMIN):
        raise HttpError(403, 'Supervisor or admin access required')


def _default_range() -> tuple[date, date]:
    today = date.today()
    return today.replace(day=1), today


@router.get('/revenue', response=DailyRevenueOut, auth=auth)
def daily_revenue(
    request,
    start: date | None = None,
    end: date | None = None,
):
    _require_supervisor_or_above(request)
    if not start or not end:
        start, end = _default_range()
    if start > end:
        raise HttpError(400, 'start must be before end')
    return ReportService.daily_revenue(start, end)


@router.get('/best-sellers', response=BestSellersOut, auth=auth)
def best_sellers(
    request,
    start: date | None = None,
    end: date | None = None,
    limit: int = 10,
):
    _require_supervisor_or_above(request)
    if not start or not end:
        start, end = _default_range()
    if start > end:
        raise HttpError(400, 'start must be before end')
    limit = min(limit, 50)
    return ReportService.best_sellers(start, end, limit)


@router.get('/inventory-valuation', response=InventoryValuationOut, auth=auth)
def inventory_valuation(request):
    _require_supervisor_or_above(request)
    return ReportService.inventory_valuation()
