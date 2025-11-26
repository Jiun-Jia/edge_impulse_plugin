"""
Configuration settings for Edge Impulse Converter Plugin
Load settings from .env file using Pydantic Settings
"""

from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for Edge Impulse Plugin"""

    ################
    ### App Info ###
    ################
    APP_NAME: Optional[str] = Field(default="Edge Impulse Plugin")
    APP_VERSION: Optional[str] = Field(default=None)
    ENVIRONMENT: Optional[Literal["development", "production"]] = Field(
        default="development"
    )

    ##########################
    ### S3 Configuration ###
    ##########################

    # S3 Endpoint URL
    # AWS S3: https://s3.amazonaws.com
    # MinIO: http://localhost:9000
    # Wasabi: https://s3.wasabisys.com
    S3_ENDPOINT_URL: Optional[str] = Field(default=None)

    S3_BUCKET: Optional[str] = Field(default=None)
    S3_REGION: Optional[str] = Field(default=None)
    S3_ACCESS_KEY: Optional[str] = Field(default=None)
    S3_SECRET_KEY: Optional[str] = Field(default=None)
    S3_USE_SSL: bool = Field(default=False)

    # S3 Base path for uploaded files
    S3_BASE_PATH: str = Field(default="edge-impulse-data")

    ##################################
    ### Edge Impulse Configuration ###
    ##################################

    # HMAC Key for signing data (optional, leave empty if not needed)
    EI_HMAC_KEY: Optional[str] = Field(default="")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()

KEY_PADDING = 40
print("=" * 100)
for key, value in vars(settings).items():
    print((f"[ENV] {key.ljust(KEY_PADDING)}: {value}"))
print("=" * 100)
