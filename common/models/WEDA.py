from pydantic import BaseModel, Field
from typing import List


##############################################
### FIXME: This Part is just a fake format ###
##############################################


class SensorData(BaseModel):
    axis: str = Field(..., description="Sensor axis name")
    unit: str = Field(..., description="Sensor unit")
    readings: List[float] = Field(..., description="Sensor readings")


class VirtualDevice(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    device_model: str = Field(..., description="Device model/type")
    sampling_interval_ms: float = Field(
        ..., description="Sampling interval in milliseconds"
    )
    sensor_data: List[SensorData] = Field(..., description="List of sensor data")
