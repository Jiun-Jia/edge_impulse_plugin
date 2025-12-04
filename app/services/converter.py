"""
Edge Impulse Data Converter Service
處理 Sensor 數據到 Edge Impulse 格式的轉換
"""

import json
import cbor2
import hmac
import time
import hashlib
import logging
from datetime import datetime
from typing import Tuple, Dict, Any

from common.models.WEDA import VirtualDevice

logger = logging.getLogger(__name__)


def weda_to_edgeimpulse(weda: VirtualDevice, hmac_key: str = "") -> Dict[str, Any]:
    """Convert WEDA Virtual Device data to EI data acquisition format.

    Args:
        weda (VirtualDevice): WEDA Virtual Device data.
        hvac_key (str, optional): EI project HVAC Key. Defaults to "".

    Returns:
        Dict[str, Any]: EI data acquisition format encoded in JSON.
    """

    # sensors list
    sensors = []
    for s in weda.sensor_data:
        sensors.append({"name": s.axis, "units": s.unit})

    # assume all sensors have same number of readings
    num = len(weda.sensor_data[0].readings)
    values = []
    for i in range(num):
        row = [s.readings[i] for s in weda.sensor_data]
        values.append(row)

    payload = {
        "device_name": weda.device_id,
        "device_type": weda.device_model,
        "interval_ms": weda.sampling_interval_ms,
        "sensors": sensors,
        "values": values,
    }

    # empty signature (all zeros). HS256 gives 32 byte signature, and we encode in hex, so we need 64 characters here
    emptySignature = "".join(["0"] * 64)

    ei_data = {
        "protected": {"ver": "v1", "alg": "HS256", "iat": time.time()},
        "signature": emptySignature,
        "payload": payload,
    }

    # encode in JSON
    encoded = json.dumps(ei_data)

    # sign message
    signature = hmac.new(
        bytes(hmac_key, "utf-8"), msg=encoded.encode("utf-8"), digestmod=hashlib.sha256
    ).hexdigest()

    # set the signature again in the message, and encode again
    ei_data["signature"] = signature
    ei_data = json.dumps(ei_data)

    return ei_data
