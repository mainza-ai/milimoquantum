"""Export module contents."""
from .celery_app import app

# Check if Celery worker is available (Redis broker reachable)
CELERY_AVAILABLE = False
try:
    import redis
    _r = redis.from_url(app.conf.broker_url)
    _r.ping()
    CELERY_AVAILABLE = True
except Exception:
    pass

__all__ = ["app", "CELERY_AVAILABLE"]
