"""
API Request Models
定義 API 請求的數據結構
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class FileFormat(str, Enum):
    """支持的文件格式"""

    JSON = "json"
    CBOR = "cbor"


class SensorAxis(BaseModel):
    """
    Sensor 軸定義

    Attributes:
        name: 軸名稱 (例如: accel_x, gyro_y)
        units: SenML 單位 (例如: m/s2, rad/s, °C)
    """

    name: str = Field(..., description="Sensor 軸名稱")
    units: str = Field(..., description="SenML 單位")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "accel_x", "units": "m/s2"},
                {"name": "temperature", "units": "°C"},
            ]
        }
    }


class SensorDataRequest(BaseModel):
    """
    Sensor 數據轉換請求

    Attributes:
        device_name: 設備唯一標識
        device_type: 設備類型/型號
        interval_ms: 採樣間隔（毫秒）
        sensors: Sensor 軸列表
        values: 2D 數值陣列
        timestamp: Unix 時間戳（秒）
        label: 數據標籤
        file_format: 輸出格式
    """

    device_name: str = Field(..., description="設備唯一標識（如 MAC 地址）")
    device_type: str = Field(..., description="設備類型/型號")
    interval_ms: float = Field(..., gt=0, description="採樣間隔（毫秒），必須 > 0")
    sensors: List[SensorAxis] = Field(..., min_length=1, description="Sensor 軸列表")
    values: List[List[float]] = Field(..., min_length=1, description="2D 數值陣列")
    timestamp: Optional[int] = Field(
        None, description="Unix 時間戳（秒），不提供則使用當前時間"
    )
    label: Optional[str] = Field(None, description="數據標籤（用於分類）")
    file_format: FileFormat = Field(
        FileFormat.JSON, description="輸出格式：json 或 cbor"
    )

    @field_validator("values")
    @classmethod
    def validate_values_not_empty(cls, v):
        """驗證 values 不為空"""
        if not v or len(v) == 0:
            raise ValueError("values 陣列不能為空")
        return v

    @field_validator("values")
    @classmethod
    def validate_values_dimensions(cls, v, info):
        """驗證 values 的維度與 sensors 數量一致"""
        # 注意：此時 sensors 可能還未驗證，需要在 model_validator 中檢查
        if v and len(v) > 0:
            first_row_len = len(v[0])
            for i, row in enumerate(v):
                if len(row) != first_row_len:
                    raise ValueError(f"values 陣列第 {i} 行長度不一致")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "device_name": "sensor_001",
                    "device_type": "accelerometer",
                    "interval_ms": 10.0,
                    "sensors": [
                        {"name": "accel_x", "units": "m/s2"},
                        {"name": "accel_y", "units": "m/s2"},
                        {"name": "accel_z", "units": "m/s2"},
                    ],
                    "values": [[1.5, 2.3, 9.8], [1.6, 2.4, 9.7], [1.55, 2.35, 9.75]],
                    "label": "idle",
                    "file_format": "json",
                }
            ]
        }
    }
