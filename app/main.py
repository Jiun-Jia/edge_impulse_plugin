"""
FastAPI Main Application
Edge Impulse Sensor Data Converter
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from logging.handlers import RotatingFileHandler
import os
from contextlib import asynccontextmanager

from app.config import settings
from app.api import converter_router, storage_router


# 配置日誌
def setup_logging():
    """配置應用日誌"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 創建 logs 目錄
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除現有的 handlers
    root_logger.handlers.clear()

    # 文件處理器（輪換）
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(file_handler)

    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    logging.info("Logging configured successfully")


# 應用生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時執行
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"S3 Endpoint: {settings.S3_ENDPOINT_URL}")
    logger.info(f"S3 Bucket: {settings.S3_BUCKET}")

    yield

    # 關閉時執行
    logger.info("Shutting down application")


# 創建 FastAPI 應用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Convert sensor data to Edge Impulse format and upload to S3-compatible storage",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(storage_router, prefix="/api/v1", tags=["Edge Impulse Storage"])
app.include_router(converter_router, prefix="/api/v1", tags=["Edge Impulse Converter"])


# 根路徑
@app.get("/", include_in_schema=False)
async def root():
    """根路徑重定向到文檔"""
    return JSONResponse(
        {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }
    )


# 全局異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局異常處理器"""
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": (
                str(exc)
                if settings.ENVIRONMENT == "development"
                else "An error occurred"
            ),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
