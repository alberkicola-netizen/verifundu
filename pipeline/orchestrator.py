from celery import Celery
import os

# ── CELERY CONFIGURATION ──────────────────────────────────────
# Redis is used as both the message broker and the result backend
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "verifundu",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["pipeline.tasks"] # We will create tasks here
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_queues={
        "pipeline": {"exchange": "pipeline", "routing_key": "pipeline"},
        "high_priority": {"exchange": "high_priority", "routing_key": "high_priority"},
    }
)

if __name__ == "__main__":
    celery_app.start()
