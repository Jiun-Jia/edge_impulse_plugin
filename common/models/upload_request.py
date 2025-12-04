from pydantic import BaseModel, Field

from .edge_impulse import UploadMetadata
from .WEDA import VirtualDevice


class UploadRequest(BaseModel):
    weda: VirtualDevice = Field(..., description="WEDA Virtual Device data")
    metadata: UploadMetadata = Field(..., description="EI upload metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "weda": {
                    "device_id": "ac:87:a3:0a:2d:1b",
                    "device_model": "test_model",
                    "sampling_interval_ms": 10,
                    "sensor_data": [
                        {
                            "axis": "accX",
                            "unit": "m/s2",
                            "readings": [-9.81, -9.83, -9.12, -9.14],
                        },
                        {
                            "axis": "accY",
                            "unit": "m/s2",
                            "readings": [0.03, 0.04, 0.03, 0.01],
                        },
                        {
                            "axis": "accZ",
                            "unit": "m/s2",
                            "readings": [1.21, 1.27, 1.23, 1.25],
                        },
                    ],
                },
                "metadata": {
                    "api_key": "ei_xxx_your_key_here",
                    "hmac_key": "your_hmac_key_here",
                    "file_name": "sample.json",
                    "label": "normal",
                    "no_label": False,
                    "dataset_type": "training",
                },
            }
        }
    }
