from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.config import config
from app.api import converter_router, ingestion_router
from app.core import lifespan


def create_app() -> FastAPI:
    # 創建 FastAPI 應用
    app = FastAPI(
        title=config.APP_NAME,
        version=config.APP_VERSION,
        description="Convert WEDA Virtual Device data to Edge Impulse format and upload to Edge Impulse Studio.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(
        converter_router, prefix="/api/v1", tags=["Edge Impulse Converter"]
    )
    app.include_router(
        ingestion_router, prefix="/api/v1", tags=["Edge Impulse Ingestion"]
    )

    return app
