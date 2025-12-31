import os
from celery import Celery

# Get Redis URL from env (default to localhost for local testing outside docker)
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "finwise_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL
)

# Standard configuration for robust task handling
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Late ack means the task is only removed from Redis AFTER it finishes successfully.
    # If the worker crashes mid-task, the task is preserved.
    task_acks_late=True,
)

# Autodiscover tasks in the 'app' module
celery_app.autodiscover_tasks(["app.tasks"])