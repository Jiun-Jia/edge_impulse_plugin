"""
API Routes
定義所有 API 端點
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from app.models import (
    SensorDataRequest,
    ConversionResponse,
    HealthCheckResponse,
    ErrorResponse,
)
from app.api.storage_routes import get_storage_client
from app.services import EdgeImpulseConverter, S3StorageClient
from app.config import settings

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/converter")

# 初始化服務
converter = EdgeImpulseConverter(hmac_key=settings.EI_HMAC_KEY or "")


@router.post(
    "/convert",
    response_model=ConversionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="轉換並上傳數據",
    description="將 Sensor 數據轉換為 Edge Impulse 格式並上傳到 S3",
    responses={
        201: {"description": "轉換成功並已上傳"},
        400: {"model": ErrorResponse, "description": "請求數據驗證失敗"},
        500: {"model": ErrorResponse, "description": "服務器內部錯誤"},
    },
)
async def convert_and_upload(request: SensorDataRequest) -> ConversionResponse:
    """
    轉換 Sensor 數據並上傳到 S3

    Args:
        request: Sensor 數據請求

    Returns:
        ConversionResponse: 轉換和上傳結果

    Raises:
        HTTPException: 轉換或上傳失敗時拋出
    """
    try:
        logger.info(
            f"Received conversion request - Device: {request.device_name}, Type: {request.device_type}"
        )

        # 轉換數據
        content, filename, content_type = converter.convert(request)
        logger.info(
            f"Data converted successfully - Filename: {filename}, Size: {len(content)} bytes"
        )

        # 獲取 S3 客戶端
        client = get_storage_client()

        # 上傳到 S3
        s3_key = client.upload_file(
            content=content,
            filename=filename,
            content_type=content_type,
            metadata={
                "device_name": request.device_name,
                "device_type": request.device_type,
                "label": request.label or "unlabeled",
            },
        )

        logger.info(f"File uploaded successfully - S3 key: {s3_key}")

        return ConversionResponse(
            status="success",
            s3_path=s3_key,
            filename=filename,
            file_size=len(content),
            endpoint=client.endpoint_url,
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Conversion/upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert or upload data: {str(e)}",
        )
