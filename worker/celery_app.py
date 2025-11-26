"""
Celery application setup for PHM service.

This module configures Celery for background task processing,
including training tasks and other asynchronous operations.
"""

import logging
from typing import Dict, Any

from celery import Celery
from celery.signals import worker_ready, task_prerun, task_postrun
from kombu import Queue

from config.settings import configs as p

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# 🔧 CELERY CONFIGURATION
# =============================================================================

# Celery broker configuration (Redis)
# Build Redis URL with optional password
if p.REDIS_PASSWORD:
    REDIS_URL = f"redis://{p.REDIS_USERNAME}:{p.REDIS_PASSWORD}@{p.REDIS_URL}"
else:
    REDIS_URL = f"redis://{p.REDIS_URL}"

# Use configured database or default to 0/1
REDIS_DB_BROKER = p.REDIS_DATABASE if p.REDIS_DATABASE else "0"
REDIS_DB_RESULT = str(int(REDIS_DB_BROKER) + 1) if REDIS_DB_BROKER.isdigit() else "1"

CELERY_BROKER_URL = f"{REDIS_URL}/{REDIS_DB_BROKER}"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/{REDIS_DB_RESULT}"

# Create Celery app
celery_app = Celery(
    "phm_service",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "domain.workers.tasks.training",
        "domain.workers.tasks.inference",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "trigger_model_training": {"queue": "training"},
        "trigger_model_inference": {"queue": "inference"},
    },
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("training", routing_key="training"),
        Queue("inference", routing_key="inference"),
    ),
    # Task execution settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=2 * 3600 + 60,  # 2 hours + 1 minute grace period
    task_soft_time_limit=2 * 3600,  # 2 hours
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Result settings
    result_expires=3600,  # 1 hour
)


# =============================================================================
# 🎯 CELERY SIGNALS
# =============================================================================


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handle worker ready signal."""
    logger.info("Celery worker is ready and waiting for tasks")


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds
):
    """Handle task pre-run signal."""
    logger.info(f"Task {task.name}[{task_id}] starting")


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **kwds,
):
    """Handle task post-run signal."""
    logger.info(f"Task {task.name}[{task_id}] finished with state: {state}")


# =============================================================================
# 🚀 HELPER FUNCTIONS
# =============================================================================


# def get_task_status(task_id: str) -> Dict[str, Any]:
#     """
#     Get status of a Celery task.

#     Args:
#         task_id: Celery task ID

#     Returns:
#         Dict containing task status and metadata
#     """
#     from .monitoring import get_task_status as _get_task_status

#     return _get_task_status(celery_app, task_id)


# def check_workers() -> Dict[str, Any]:
#     """
#     Check if Celery workers are running and get their status.

#     Returns:
#         Dict containing worker status information
#     """
#     from .monitoring import check_workers as _check_workers

#     return _check_workers(celery_app)


# def check_task_on_workers(task_name: str) -> Dict[str, Any]:
#     """
#     Check which workers can handle a specific task and their current status.

#     Args:
#         task_name: Name of the task to check (e.g., "trigger_model_training")

#     Returns:
#         Dict containing task-specific worker information
#     """
#     from .monitoring import check_task_on_workers as _check_task_on_workers

#     return _check_task_on_workers(celery_app, task_name)


# def check_queue_workers(queue_name: str) -> Dict[str, Any]:
#     """
#     Check if workers are active for a specific queue.

#     Args:
#         queue_name: Name of the queue to check (e.g., "training", "inference", "default")

#     Returns:
#         Dict containing queue-specific worker information
#     """
#     from .monitoring import check_queue_workers as _check_queue_workers

#     return _check_queue_workers(celery_app, queue_name)


# def check_all_queues() -> Dict[str, Any]:
#     """
#     Check the status of all configured queues.

#     Returns:
#         Dict containing information about all queues and their workers
#     """
#     from .monitoring import check_all_queues as _check_all_queues

#     return _check_all_queues(celery_app)


# def cancel_task(task_id: str) -> bool:
#     """
#     Cancel a running Celery task.

#     Args:
#         task_id: Celery task ID

#     Returns:
#         True if cancelled successfully
#     """
#     from .monitoring import cancel_task as _cancel_task

#     return _cancel_task(celery_app, task_id)


if __name__ == "__main__":
    # For development - start worker directly
    celery_app.start()
