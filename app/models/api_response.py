"""
API Response Models
定義 API 響應的數據結構
"""

from pydantic import BaseModel, Field
from typing import Optional


class ConversionResponse(BaseModel):
    """
    數據轉換響應

    Attributes:
        status: 操作狀態
        s3_path: S3 對象路徑
        filename: 生成的文件名
        file_size: 文件大小（字節）
        endpoint: S3 endpoint URL
    """

    status: str = Field(..., description="操作狀態")
    s3_path: str = Field(..., description="S3 對象路徑")
    filename: str = Field(..., description="生成的文件名")
    file_size: int = Field(..., description="文件大小（字節）")
    endpoint: Optional[str] = Field(None, description="S3 endpoint URL")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "s3_path": "edge-impulse-data/accelerometer_idle_1699123456789.json",
                    "filename": "accelerometer_idle_1699123456789.json",
                    "file_size": 2048,
                    "endpoint": "http://localhost:9000",
                }
            ]
        }
    }


class HealthCheckResponse(BaseModel):
    """
    健康檢查響應

    Attributes:
        status: 服務狀態
        message: 狀態訊息
        s3_connected: S3 連接狀態
    """

    status: str = Field(..., description="服務狀態")
    message: str = Field(default="Service is running", description="狀態訊息")
    s3_connected: Optional[bool] = Field(None, description="S3 連接狀態")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "ok", "message": "Service is running", "s3_connected": True}
            ]
        }
    }


class ErrorResponse(BaseModel):
    """
    錯誤響應

    Attributes:
        status: 錯誤狀態
        message: 錯誤訊息
        detail: 詳細錯誤信息
    """

    status: str = Field(default="error", description="錯誤狀態")
    message: str = Field(..., description="錯誤訊息")
    detail: Optional[str] = Field(None, description="詳細錯誤信息")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "error",
                    "message": "Validation failed",
                    "detail": "Sensor count doesn't match value dimensions",
                }
            ]
        }
    }
