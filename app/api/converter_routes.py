"""
API Routes
定義所有 API 端點
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core import get_session
from common.models import UploadRequest
from app.services.converter import weda_to_edgeimpulse
from worker.tasks.ei_task import convert_and_upload
from common.config import config
from logs import router_logger as logger


# 創建路由器
router = APIRouter(prefix="/converter")


@router.post("/weda_to_edgeimpulse")
async def ingest(upload_request: UploadRequest, session=Depends(get_session)):
    weda = upload_request.weda
    metadata = upload_request.metadata
    # Convert WEDA to EI format
    ei_data = weda_to_edgeimpulse(weda, hmac_key=metadata.hmac_key)

    headers = (
        {
            "Content-Type": "application/json",
            "x-file-name": metadata.file_name or "data.json",
            "x-label": metadata.label,
            "x-no-label": "1" if metadata.no_label else "0",
            "x-api-key": metadata.api_key,
        },
    )
    print(f"{headers=}")

    async with session.post(
        f"https://ingestion.edgeimpulse.com/api/{metadata.dataset_type.value}/data",
        headers={
            "Content-Type": "application/json",
            "x-file-name": metadata.file_name or "data.json",
            "x-label": metadata.label,
            "x-no-label": "1" if metadata.no_label else "0",
            "x-api-key": metadata.api_key,
        },
        data=ei_data,
        timeout=30,
    ) as res:
        print(res)
        res.raise_for_status()

    return {"status": "success", "message": "Data ingested to Edge Impulse"}


@router.post("/weda_to_edgeimpulse_with_worker")
def weda_to_edgeimpulse_with_worker(upload_request: UploadRequest):
    task = convert_and_upload.delay(upload_request.model_dump())
    logger.info(f"Task submitted with ID: {task.id}")

    return {
        "status": "submitted",
        "message": "Conversion and upload task submitted",
        "task_id": task.id,
    }
