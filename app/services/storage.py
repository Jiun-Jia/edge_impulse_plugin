"""
S3-Compatible Storage Service
支持 AWS S3、MinIO、Wasabi 等 S3 兼容存儲服務
"""

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from pathlib import Path
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class S3StorageClient:
    """
    S3 兼容存儲客戶端

    支持多種 S3 兼容服務：
    - AWS S3
    - MinIO
    - Wasabi
    - 其他 S3 兼容服務
    """

    def __init__(
        self,
        endpoint_url: str,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        use_ssl: bool = True,
        base_path: str = "",
    ):
        """
        初始化 S3 客戶端

        Args:
            endpoint_url: S3 endpoint URL
            bucket: Bucket 名稱
            region: 區域名稱
            access_key: Access Key ID
            secret_key: Secret Access Key
            use_ssl: 是否使用 SSL
            base_path: 基礎路徑
        """
        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self._access_key = access_key
        self._secret_key = secret_key
        self.region = region
        self.use_ssl = use_ssl
        self.base_path = base_path

        # 對於 AWS S3，endpoint_url 設為 None
        endpoint = None if endpoint_url == "https://s3.amazonaws.com" else endpoint_url

        try:
            self.client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                use_ssl=use_ssl,
                verify=use_ssl,
            )
            logger.info(
                f"S3 client initialized - Endpoint: {endpoint_url}, Bucket: {bucket}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """
        測試 S3 連接

        Returns:
            True 如果連接成功，否則 False
        """
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"S3 connection test successful - Bucket: {self.bucket}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(
                f"S3 connection test failed - {error_code}: {e.response['Error']['Message']}"
            )
            return False
        except Exception as e:
            logger.error(f"S3 connection test failed - {str(e)}")
            return False

    def upload_file(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        上傳文件到 S3

        Args:
            content: 文件內容（bytes）
            filename: 文件名
            content_type: MIME 類型
            metadata: 額外的元數據（可選）

        Returns:
            S3 對象的 key

        Raises:
            Exception: 上傳失敗時拋出異常
        """
        try:
            # 構建完整路徑
            s3_key = f"{self.base_path}/{filename}"

            # 準備元數據
            upload_metadata = metadata or {}
            upload_metadata["uploaded_by"] = "edge-impulse-converter"

            # 上傳文件
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                Metadata=upload_metadata,
            )

            logger.info(
                f"File uploaded successfully - S3 key: {s3_key}, Size: {len(content)} bytes"
            )
            return s3_key

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            logger.error(f"S3 upload failed - {error_code}: {error_msg}")
            raise Exception(f"S3 upload failed: {error_code} - {error_msg}")
        except Exception as e:
            logger.error(f"S3 upload failed - {str(e)}")
            raise Exception(f"S3 upload failed: {str(e)}")

    def generate_presigned_url(
        self, s3_key: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        生成預簽名 URL

        Args:
            s3_key: S3 對象 key
            expiration: URL 有效期（秒），默認 1 小時

        Returns:
            預簽名 URL，失敗返回 None
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": s3_key},
                ExpiresIn=expiration,
            )
            logger.debug(f"Generated presigned URL for {s3_key}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return None

    def list_files(
        self, prefix: Optional[str] = None, max_keys: int = 1000
    ) -> List[Dict]:
        """
        列出 S3 bucket 中的文件

        Args:
            prefix: 路徑前綴過濾（可選）
            max_keys: 最大返回數量

        Returns:
            文件對象列表
        """
        try:
            list_prefix = prefix or self.base_path

            response = self.client.list_objects_v2(
                Bucket=self.bucket, Prefix=list_prefix, MaxKeys=max_keys
            )

            files = response.get("Contents", [])
            logger.info(f"Listed {len(files)} files from S3 - Prefix: {list_prefix}")
            return files

        except ClientError as e:
            logger.error(f"Failed to list files: {str(e)}")
            raise

    def delete_file(self, s3_key: str) -> bool:
        """
        刪除 S3 文件

        Args:
            s3_key: S3 對象 key

        Returns:
            True 如果刪除成功
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info(f"File deleted successfully - S3 key: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise

    def get_file_info(self, s3_key: str) -> Optional[Dict]:
        """
        獲取文件信息

        Args:
            s3_key: S3 對象 key

        Returns:
            文件元數據字典，如果不存在返回 None
        """
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=s3_key)
            info = {
                "size": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "metadata": response.get("Metadata", {}),
            }
            logger.debug(f"Retrieved file info for {s3_key}")
            return info
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                logger.warning(f"File not found: {s3_key}")
                return None
            logger.error(f"Failed to get file info: {str(e)}")
            raise e

    def generate_s3_uri(self, s3_key: str) -> str:
        """
        生成 S3 URI

        Args:
            s3_key: S3 對象 key

        Returns:
            完整的 S3 URI
        """
        if self.endpoint_url == "https://s3.amazonaws.com":
            return f"s3://{self.bucket}/{s3_key}"
        else:
            # 對於自定義 endpoint（MinIO、Wasabi 等）
            return f"{self.endpoint_url}/{self.bucket}/{s3_key}"
