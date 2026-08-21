from celery import Celery
from app.core.config import settings

def create_celery_app() -> Celery:
    app = Celery(
        "cybersec_worker",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
    )
    app.config_from_object({
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
        "task_track_started": True,
        "task_acks_late": True,
        "worker_prefetch_multiplier": 1,
        "task_routes": {
            "app.workers.scan_tasks.*": {"queue": "scans"},
        },
    })
    return app

celery_app = create_celery_app()
