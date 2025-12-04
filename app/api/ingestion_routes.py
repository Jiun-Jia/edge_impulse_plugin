"""
Define API w/ Ingestion API
"""

from fastapi import APIRouter, HTTPException
import logging
from celery.result import AsyncResult

from common.config import config
from worker.celery_app import celery_app
from worker.tasks.ei_task import upload_to_edge

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/EI_ingestion")

INGESTION_ENDPOINT = config.EI_INGESTION_ENDPOINT

# Test config
API_KEY = "ei_1df40caea3a8ff4b9869f87c5fef6f3408a7e89982cac9ddd017e964fcbca70a"


@router.post("/data")
async def ingest_data(data):
    #############################
    ### TODO: Save data to DB ###
    #############################
    # data_id = save_data(data)
    data_id = "test_data_id"

    # 排入 Celery 任務
    task = upload_to_edge.delay(data_id)

    # 直接回應 202 Accepted，回傳 task_id
    return {"message": "Task submitted", "task_id": task.id}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "state": task_result.state,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    }
