from ninja import Router
from ninja import Schema
from django.db import connection, OperationalError
from decouple import config
import redis as redis_lib

router = Router(tags=['Health'])


class ServiceStatus(Schema):
    status: str
    error: str | None = None


class HealthOut(Schema):
    status: str
    services: dict


def _check_database() -> ServiceStatus:
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return ServiceStatus(status='healthy')
    except OperationalError as e:
        return ServiceStatus(status='unhealthy', error=str(e))


def _check_redis() -> ServiceStatus:
    try:
        r = redis_lib.from_url(config('REDIS_URL', default='redis://localhost:6379/0'))
        r.ping()
        return ServiceStatus(status='healthy')
    except Exception as e:
        return ServiceStatus(status='unhealthy', error=str(e))


@router.get('/', response=HealthOut, auth=None)
def health(request):
    db = _check_database()
    redis = _check_redis()

    all_healthy = db.status == 'healthy' and redis.status == 'healthy'

    return HealthOut(
        status='healthy' if all_healthy else 'unhealthy',
        services={
            'database': db.model_dump(),
            'redis': redis.model_dump(),
        },
    )
