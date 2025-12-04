"""
FastAPI Main Application
Edge Impulse Sensor Data Converter
"""

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse

from common.config import config
from logs import system_logger as logger

# from app.api import converter_router, storage_router, ingestion_router
# from app.core import lifespan
from app.factory import create_app

# # 創建 FastAPI 應用
# app = FastAPI(
#     title=config.APP_NAME,
#     version=config.APP_VERSION,
#     description="Convert WEDA Virtual Device data to Edge Impulse format and upload to Edge Impulse Studio.",
#     lifespan=lifespan,
#     docs_url="/docs",
#     redoc_url="/redoc",
#     openapi_url="/openapi.json",
# )

# # CORS 中間件
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 註冊路由
# app.include_router(storage_router, prefix="/api/v1", tags=["Edge Impulse Storage"])
# app.include_router(converter_router, prefix="/api/v1", tags=["Edge Impulse Converter"])
# app.include_router(ingestion_router, prefix="/api/v1", tags=["Edge Impulse Ingestion"])


# # 根路徑
# @app.get("/", include_in_schema=False)
# async def root():
#     """根路徑重定向到文檔"""
#     return JSONResponse(
#         {
#             "message": f"Welcome to {config.APP_NAME}",
#             "version": config.APP_VERSION,
#             "docs": "/docs",
#             "redoc": "/redoc",
#         }
#     )

app = create_app()

if __name__ == "__main__":
    # List all config values on startup
    KEY_PADDING = 40
    logger.info("=" * 100)
    for key, value in vars(config).items():
        logger.info((f"[ENV] {key.ljust(KEY_PADDING)}: {value}"))
    logger.info("=" * 100)

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=6969,
        reload=False,
    )
