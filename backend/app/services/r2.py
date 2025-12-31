import uuid
from datetime import timedelta
from typing import Tuple, Optional
import boto3
from botocore.config import Config
from app.config import settings


class R2Service:
    """Cloudflare R2 storage service for video uploads/downloads."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy initialization of R2 client (S3-compatible)."""
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
        return self._client

    def generate_upload_url(
        self,
        filename: str,
        content_type: str = "video/mp4",
        expiration_seconds: int = 900  # 15 minutes
    ) -> Tuple[str, str]:
        """
        Generate a presigned URL for uploading a video.

        Args:
            filename: Original filename
            content_type: MIME type of the file
            expiration_seconds: URL expiration time in seconds

        Returns:
            Tuple of (presigned_url, object_key)
        """
        # Generate unique object path
        video_id = uuid.uuid4()
        object_key = f"videos/{video_id}/{filename}"

        url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expiration_seconds,
        )

        return url, object_key

    def generate_download_url(
        self,
        object_key: str,
        expiration_seconds: int = 3600  # 60 minutes
    ) -> str:
        """
        Generate a presigned URL for downloading/viewing a video.

        Args:
            object_key: The object path in R2
            expiration_seconds: URL expiration time in seconds

        Returns:
            Presigned download URL
        """
        url = self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": object_key,
            },
            ExpiresIn=expiration_seconds,
        )

        return url

    def delete_object(self, object_key: str) -> bool:
        """
        Delete an object from R2.

        Args:
            object_key: The object path to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=object_key,
            )
            return True
        except Exception:
            return False

    def object_exists(self, object_key: str) -> bool:
        """
        Check if an object exists.

        Args:
            object_key: The object path to check

        Returns:
            True if exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=object_key,
            )
            return True
        except Exception:
            return False

    def get_object_metadata(self, object_key: str) -> Optional[dict]:
        """
        Get metadata for an object.

        Args:
            object_key: The object path

        Returns:
            Dict with metadata or None if not found
        """
        try:
            response = self.client.head_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=object_key,
            )
            return {
                "key": object_key,
                "size": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
            }
        except Exception:
            return None
