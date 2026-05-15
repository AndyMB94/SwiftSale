import redis as redis_lib
from decouple import config
from django.db import OperationalError, connection
from ninja import Router, Schema

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


def _check_celery() -> ServiceStatus:
    try:
        from config.celery import app as celery_app
        result = celery_app.control.ping(timeout=2)
        if result:
            return ServiceStatus(status='healthy')
        return ServiceStatus(status='unhealthy', error='No workers responded')
    except Exception as e:
        return ServiceStatus(status='unhealthy', error=str(e))


@router.get('/', response=HealthOut, auth=None)
def health(request):
    db = _check_database()
    redis = _check_redis()
    celery = _check_celery()

    all_healthy = all(
        s.status == 'healthy' for s in [db, redis, celery]
    )

    return HealthOut(
        status='healthy' if all_healthy else 'unhealthy',
        services={
            'database': db.model_dump(),
            'redis': redis.model_dump(),
            'celery': celery.model_dump(),
        },
    )
