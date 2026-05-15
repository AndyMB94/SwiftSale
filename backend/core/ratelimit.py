from functools import wraps
from django_redis import get_redis_connection
from ninja.errors import HttpError


def rate_limit(rate: str = '10/m'):
    """
    IP-based rate limiter backed by Redis (django-redis cache).
    Uses atomic INCR + EXPIRE pipeline — no race condition.

    Usage:
        @router.post('/login', ...)
        def login(request, ...):
            check_rate_limit(request, rate='10/m')
            ...
    """
    count_str, _, period = rate.partition('/')
    max_requests = int(count_str)
    window = {'s': 1, 'm': 60, 'h': 3600}.get(period, 60)

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            _enforce(request, func.__name__, max_requests, window)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_rate_limit(request, key_prefix: str = 'default', rate: str = '10/m') -> None:
    """Inline rate-limit check — call directly inside a view function."""
    count_str, _, period = rate.partition('/')
    max_requests = int(count_str)
    window = {'s': 1, 'm': 60, 'h': 3600}.get(period, 60)
    _enforce(request, key_prefix, max_requests, window)


def _enforce(request, name: str, max_requests: int, window: int) -> None:
    ip = _get_ip(request)
    key = f'ratelimit:{name}:{ip}'

    try:
        r = get_redis_connection('default')
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        results = pipe.execute()
        current = results[0]
    except Exception:
        # Redis unavailable — fail open (do not block the request)
        return

    if current > max_requests:
        raise HttpError(429, 'Too many requests. Please try again later.')


def _get_ip(request) -> str:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')
