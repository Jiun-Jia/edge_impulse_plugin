"""
Storage API Routes
S3 存儲相關的 API 端點
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, List, Optional
import logging

from app.models import HealthCheckResponse
from app.services import S3StorageClient
from app.config import settings

logger = logging.getLogger(__name__)

# 創建存儲路由器
router = APIRouter(prefix="/storage")

# S3 客戶端（單例模式）
_storage_client: Optional[S3StorageClient] = None


def get_storage_client() -> S3StorageClient:
    """獲取 S3 存儲客戶端（單例模式）"""
    global _storage_client
    if _storage_client is None:
        if not all(
            [
                settings.S3_ENDPOINT_URL,
                settings.S3_BUCKET,
                settings.S3_ACCESS_KEY,
                settings.S3_SECRET_KEY,
            ]
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 configuration is incomplete. Please check environment variables.",
            )

        _storage_client = S3StorageClient(
            endpoint_url=settings.S3_ENDPOINT_URL,
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            use_ssl=settings.S3_USE_SSL,
            base_path=settings.S3_BASE_PATH,
        )
    return _storage_client


@router.get(
    "/status",
    response_model=HealthCheckResponse,
    summary="S3 連接狀態檢查",
    description="檢查 S3 存儲服務的連接狀態，驗證 endpoint、bucket 訪問權限和可用性",
)
async def check_storage_status() -> HealthCheckResponse:
    """
    檢查 S3 存儲連接狀態

    此端點會執行以下檢查：
    - S3 endpoint 可達性
    - Bucket 存在性
    - 訪問權限驗證

    Returns:
        HealthCheckResponse: S3 連接狀態

    Status 說明：
        - "ok": S3 連接正常
        - "error": S3 連接失敗或配置錯誤
    """
    try:
        client = get_storage_client()
        s3_connected = client.test_connection()

        if s3_connected:
            return HealthCheckResponse(
                status="ok",
                message=f"S3 storage connected successfully to {client.bucket}",
                s3_connected=True,
            )
        else:
            return HealthCheckResponse(
                status="error",
                message="S3 connection failed. Please check configuration.",
                s3_connected=False,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Storage status check failed: {str(e)}")
        return HealthCheckResponse(
            status="error",
            message=f"Storage check failed: {str(e)}",
            s3_connected=False,
        )


@router.get(
    "/config",
    summary="獲取存儲配置信息",
    description="獲取當前 S3 存儲配置（敏感信息已脫敏）",
)
async def get_storage_config() -> Dict[str, Any]:
    """
    獲取 S3 存儲配置信息

    Returns:
        Dict: 存儲配置信息（access key 和 secret key 已脫敏）
    """
    try:
        client = get_storage_client()

        # 脫敏處理
        access_key_masked = (
            client._access_key[:4] + "****" + client._access_key[-4:]
            if settings.S3_ACCESS_KEY
            else "****"
        )
        secret_key_masked = (
            client._secret_key[:4] + "****" + client._secret_key[-4:]
            if settings.S3_SECRET_KEY
            else "****"
        )

        return {
            "endpoint": client.endpoint_url,
            "bucket": client.bucket,
            "region": client.region,
            "use_ssl": client.use_ssl,
            "access_key": access_key_masked,
            "secret_key": secret_key_masked,
            "base_path": client.base_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get storage config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage configuration: {str(e)}",
        )


@router.get(
    "/files",
    summary="列出已上傳的文件",
    description="列出 S3 存儲中已上傳的 Edge Impulse 數據文件",
)
async def list_storage_files(
    prefix: Optional[str] = Query(None, description="路徑前綴過濾"),
    max_keys: int = Query(100, ge=1, le=1000, description="最大返回數量（1-1000）"),
) -> Dict[str, Any]:
    """
    列出 S3 存儲中的文件

    Args:
        prefix: 路徑前綴過濾（可選）
        max_keys: 最大返回數量（默認 100，範圍 1-1000）

    Returns:
        Dict: 包含文件列表的響應
    """
    try:
        client = get_storage_client()
        files = client.list_files(prefix=prefix, max_keys=max_keys)

        return {
            "status": "success",
            "count": len(files),
            "prefix": prefix,
            "files": [
                {
                    "key": f.get("Key"),
                    "size": f.get("Size"),
                    "last_modified": (
                        f.get("LastModified").isoformat()
                        if f.get("LastModified")
                        else None
                    ),
                }
                for f in files
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}",
        )


@router.get(
    "/files/{file_key:path}",
    summary="獲取文件信息",
    description="獲取指定文件的元數據信息",
)
async def get_file_info(file_key: str) -> Dict[str, Any]:
    """
    獲取文件元數據信息

    Args:
        file_key: 文件的 S3 key（路徑）

    Returns:
        Dict: 文件元數據信息
    """
    try:
        client = get_storage_client()
        file_info = client.get_file_info(file_key)

        if file_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_key}",
            )

        return {
            "status": "success",
            "key": file_key,
            "info": {
                "size": file_info.get("size"),
                "content_type": file_info.get("content_type"),
                "last_modified": (
                    file_info.get("last_modified").isoformat()
                    if file_info.get("last_modified")
                    else None
                ),
                "metadata": file_info.get("metadata", {}),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get file info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file info: {str(e)}",
        )


@router.delete(
    "/files/{file_key:path}", summary="刪除文件", description="從 S3 存儲中刪除指定文件"
)
async def delete_file(file_key: str) -> Dict[str, Any]:
    """
    刪除 S3 存儲中的文件

    Args:
        file_key: 文件的 S3 key（路徑）

    Returns:
        Dict: 刪除操作結果
    """
    try:
        client = get_storage_client()
        success = client.delete_file(file_key)

        if success:
            return {
                "status": "success",
                "message": f"File deleted successfully: {file_key}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )


@router.get(
    "/files/{file_key:path}/url",
    summary="生成文件預簽名 URL",
    description="生成文件的臨時訪問 URL",
    deprecated=True,
)
async def generate_file_url(
    file_key: str,
    expiration: int = Query(
        3600,
        ge=60,
        le=604800,
        description="URL 有效期（秒），範圍 60-604800（1分鐘到7天）",
    ),
) -> Dict[str, Any]:
    """
    生成文件的預簽名 URL

    Args:
        file_key: 文件的 S3 key（路徑）
        expiration: URL 有效期（秒），默認 3600（1小時）

    Returns:
        Dict: 包含預簽名 URL 的響應
    """
    try:
        client = get_storage_client()
        url = client.generate_presigned_url(file_key, expiration=expiration)

        if url is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate presigned URL",
            )

        return {
            "status": "success",
            "key": file_key,
            "url": url,
            "expires_in": expiration,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate URL: {str(e)}",
        )
