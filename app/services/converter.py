"""
Edge Impulse Data Converter Service
處理 Sensor 數據到 Edge Impulse 格式的轉換
"""

import json
import cbor2
import hmac
import hashlib
from datetime import datetime
from typing import Tuple
import logging

from app.models import SensorDataRequest, FileFormat
from app.models.edge_impulse import (
    EdgeImpulseData,
    EdgeImpulsePayload,
    ProtectedHeader,
    SensorAxisInfo,
)

logger = logging.getLogger(__name__)


class EdgeImpulseConverter:
    """
    Edge Impulse 數據轉換器

    負責將 Sensor 數據轉換為 Edge Impulse 標準格式（JSON 或 CBOR）
    """

    def __init__(self, hmac_key: str = ""):
        """
        初始化轉換器

        Args:
            hmac_key: HMAC 密鑰，用於數據簽名（可選）
        """
        self.hmac_key = hmac_key
        logger.info(
            f"EdgeImpulseConverter initialized - HMAC enabled: {bool(hmac_key)}"
        )

    def _sign_data(self, data: dict) -> str:
        """
        使用 HMAC-SHA256 簽名數據

        Args:
            data: 要簽名的字典數據

        Returns:
            64 字符的 hex 簽名，如果沒有密鑰則返回 "0"*64
        """
        if not self.hmac_key:
            logger.debug("No HMAC key provided, returning empty signature")
            return "0" * 64

        try:
            # 創建副本並設置臨時簽名
            data_copy = data.copy()
            data_copy["signature"] = "0" * 64

            # 序列化為 JSON（無空白）
            json_str = json.dumps(data_copy, separators=(",", ":"), sort_keys=True)

            # 生成 HMAC 簽名
            signature = hmac.new(
                self.hmac_key.encode("utf-8"), json_str.encode("utf-8"), hashlib.sha256
            ).digest()

            hex_signature = signature.hex()
            logger.debug(
                f"Data signed successfully - Signature: {hex_signature[:16]}..."
            )
            return hex_signature

        except Exception as e:
            logger.error(f"Failed to sign data: {str(e)}")
            raise

    def _build_edge_impulse_payload(self, request: SensorDataRequest) -> dict:
        """
        構建 Edge Impulse 標準格式的 payload

        Args:
            request: Sensor 數據請求

        Returns:
            符合 Edge Impulse 規範的字典
        """
        # 構建 protected header
        protected = {
            "ver": "v1",
            "alg": "HS256" if self.hmac_key else "none",
            "iat": request.timestamp or int(datetime.now().timestamp()),
        }

        # 構建 payload
        payload = {
            "device_name": request.device_name,
            "device_type": request.device_type,
            "interval_ms": request.interval_ms,
            "sensors": [
                {"name": sensor.name, "units": sensor.units}
                for sensor in request.sensors
            ],
            "values": request.values,
        }

        # 組合完整結構
        ei_data = {
            "protected": protected,
            "signature": "0" * 64,  # 臨時簽名
            "payload": payload,
        }

        # 簽名數據
        ei_data["signature"] = self._sign_data(ei_data)

        logger.debug(f"Edge Impulse payload built for device: {request.device_name}")
        return ei_data

    def _validate_dimensions(self, request: SensorDataRequest) -> None:
        """
        驗證數據維度是否匹配

        Args:
            request: Sensor 數據請求

        Raises:
            ValueError: 如果 sensors 數量與 values 維度不匹配
        """
        sensor_count = len(request.sensors)
        value_dimensions = len(request.values[0]) if request.values else 0

        if sensor_count != value_dimensions:
            error_msg = (
                f"Sensor count ({sensor_count}) doesn't match "
                f"value dimensions ({value_dimensions})"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"Dimension validation passed - {sensor_count} sensors")

    def _generate_filename(
        self, request: SensorDataRequest, file_format: FileFormat
    ) -> str:
        """
        生成文件名

        Args:
            request: Sensor 數據請求
            file_format: 文件格式

        Returns:
            生成的文件名
        """
        # 標籤部分
        label_part = f"_{request.label}" if request.label else ""

        # 時間戳（毫秒）
        timestamp = int(datetime.now().timestamp() * 1000)

        # 組合文件名
        extension = file_format.value
        filename = f"{request.device_type}{label_part}_{timestamp}.{extension}"

        logger.debug(f"Generated filename: {filename}")
        return filename

    def convert(self, request: SensorDataRequest) -> Tuple[bytes, str, str]:
        """
        轉換 Sensor 數據為 Edge Impulse 格式

        Args:
            request: Sensor 數據請求

        Returns:
            Tuple[bytes, str, str]: (文件內容, 文件名, Content-Type)

        Raises:
            ValueError: 數據驗證失敗
        """
        logger.info(f"Starting conversion for device: {request.device_name}")

        # 驗證數據維度
        self._validate_dimensions(request)

        # 構建 Edge Impulse payload
        ei_payload = self._build_edge_impulse_payload(request)

        # 生成文件名
        filename = self._generate_filename(request, request.file_format)

        # 轉換為指定格式
        if request.file_format == FileFormat.CBOR:
            content = cbor2.dumps(ei_payload)
            content_type = "application/cbor"
            logger.info(f"Converted to CBOR format - Size: {len(content)} bytes")
        else:
            # JSON 格式（帶縮進）
            content = json.dumps(ei_payload, indent=2).encode("utf-8")
            content_type = "application/json"
            logger.info(f"Converted to JSON format - Size: {len(content)} bytes")

        return content, filename, content_type
