"""
Edge Impulse Data Format Models
定義 Edge Impulse 數據格式的結構
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal


class ProtectedHeader(BaseModel):
    """
    Edge Impulse Protected Header

    Attributes:
        ver: 版本號，固定為 "v1"
        alg: 簽名算法 (HS256 或 none)
        iat: 創建時間戳（秒）
    """

    ver: Literal["v1"] = Field(default="v1", description="版本號")
    alg: Literal["HS256", "none"] = Field(..., description="簽名算法")
    iat: int = Field(..., description="創建時間戳（Unix 秒）")


class SensorAxisInfo(BaseModel):
    """
    Sensor 軸信息

    Attributes:
        name: 軸名稱
        units: SenML 單位
    """

    name: str = Field(..., description="軸名稱")
    units: str = Field(..., description="SenML 單位")


class EdgeImpulsePayload(BaseModel):
    """
    Edge Impulse Payload 數據

    Attributes:
        device_name: 設備名稱
        device_type: 設備類型
        interval_ms: 採樣間隔
        sensors: Sensor 軸列表
        values: 數值陣列
    """

    device_name: str = Field(..., description="設備名稱")
    device_type: str = Field(..., description="設備類型")
    interval_ms: float = Field(..., description="採樣間隔（毫秒）")
    sensors: List[SensorAxisInfo] = Field(..., description="Sensor 軸列表")
    values: List[List[float]] = Field(..., description="數值陣列")


class EdgeImpulseData(BaseModel):
    """
    完整的 Edge Impulse 數據結構

    Attributes:
        protected: Protected header
        signature: HMAC-SHA256 簽名（64 字符 hex）
        payload: 實際數據
    """

    protected: ProtectedHeader = Field(..., description="Protected header")
    signature: str = Field(..., description="HMAC-SHA256 簽名")
    payload: EdgeImpulsePayload = Field(..., description="實際數據")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "protected": {"ver": "v1", "alg": "HS256", "iat": 1699000000},
                    "signature": "0" * 64,
                    "payload": {
                        "device_name": "sensor_001",
                        "device_type": "accelerometer",
                        "interval_ms": 10.0,
                        "sensors": [
                            {"name": "accel_x", "units": "m/s2"},
                            {"name": "accel_y", "units": "m/s2"},
                            {"name": "accel_z", "units": "m/s2"},
                        ],
                        "values": [[1.5, 2.3, 9.8], [1.6, 2.4, 9.7]],
                    },
                }
            ]
        }
    }
