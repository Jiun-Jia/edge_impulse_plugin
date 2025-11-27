"""
Celery application setup for PHM service.

This module configures Celery for background task processing,
including training tasks and other asynchronous operations.
"""

from celery import Celery
from kombu import Queue

from common.config import config


# Create Celery app
def create_celery_app() -> Celery:
    """Create and configure Celery application."""
    app = Celery(
        "Edge_Impulse_Plugin",
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_RESULT_BACKEND,
        include=[
            "worker.tasks.ei_task",
        ],
    )

    # Celery configuration
    app.conf.update(
        # Serializer settings
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # Timezone settings
        timezone="UTC",
        enable_utc=True,
        # Queue configuration
        task_default_queue="default",
        task_queues=(
            Queue("default"),
            Queue("EI_ingestion", routing_key="EI_ingestion"),
        ),
        # Task execution settings
        task_reject_on_worker_lost=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_time_limit=2 * 3600 + 60,  # 2 hours + 1 minute grace period
        task_soft_time_limit=2 * 3600,  # 2 hours
        # Retry settings
        task_default_retry_delay=60,  # 1 minute
        task_max_retries=3,
        # Result settings
        result_persistent=False,
        result_expires=3600,  # 1 hour
        # Redis Backend setting
        redis_backend_health_check_interval=30,
        redis_socket_timeout=5,
        # Worker settings
        worker_pool="solo",
    )
    return app


celery_app = create_celery_app()
