"""
API Response Models
定義 API 響應的數據結構
"""

from typing import Optional
from pydantic import BaseModel, Field


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
