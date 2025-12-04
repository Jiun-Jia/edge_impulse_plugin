"""
Edge Impulse Data Format Models
定義 Edge Impulse 數據格式的結構
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class DatasetType(str, Enum):
    TRAINING = "training"
    TESTING = "testing"


# Metadata for uploading to Edge Impulse
class UploadMetadata(BaseModel):
    ################################
    ### FIXME: To remove the key ###
    ################################
    api_key: str = Field(
        default="ei_1df40caea3a8ff4b9869f87c5fef6f3408a7e89982cac9ddd017e964fcbca70a",
        description="Edge Impulse API Key",
    )
    hmac_key: str = Field(
        default="e45689eb5df362d610ea2f8cc3661a7d",
        description="HMAC Key for signing data",
    )
    file_name: Optional[str] = Field(
        default=None, description="File name on Edge Impulse"
    )
    label: Optional[str] = Field(default=None, description="Data label")
    no_label: bool = Field(default=False, description="Whether the data has no label")
    dataset_type: DatasetType = Field(
        default=DatasetType.TRAINING, description="Dataset type for upload"
    )

    @model_validator(mode="after")
    def enforce_no_label_logic(self):
        # 如果 file_name 和 label 都沒有設定 → 強制 no_label = True
        if self.file_name is None and self.label is None:
            object.__setattr__(self, "no_label", True)
        return self
