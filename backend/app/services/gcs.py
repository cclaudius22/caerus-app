import uuid
from datetime import timedelta
from typing import Tuple, Optional
from google.cloud import storage
from google.oauth2 import service_account
from app.config import settings


class GCSService:
    """Google Cloud Storage service for video uploads/downloads."""

    def __init__(self):
        self._client = None
        self._bucket = None
        self._credentials = None

    @property
    def credentials(self):
        """Load service account credentials for signing URLs."""
        if self._credentials is None:
            self._credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
        return self._credentials

    @property
    def client(self):
        """Lazy initialization of GCS client with service account."""
        if self._client is None:
            self._client = storage.Client(credentials=self.credentials)
        return self._client

    @property
    def bucket(self):
        """Get the configured bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
        return self._bucket

    def generate_upload_url(
        self,
        filename: str,
        content_type: str = "video/mp4",
        expiration_seconds: int = 900  # 15 minutes
    ) -> Tuple[str, str]:
        """
        Generate a signed URL for uploading a video.

        Args:
            filename: Original filename
            content_type: MIME type of the file
            expiration_seconds: URL expiration time in seconds

        Returns:
            Tuple of (signed_url, object_key)
        """
        # Generate unique object path
        video_id = uuid.uuid4()
        object_key = f"videos/{video_id}/{filename}"

        blob = self.bucket.blob(object_key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration_seconds),
            method="PUT",
            content_type=content_type,
        )

        return url, object_key

    def generate_download_url(
        self,
        object_key: str,
        expiration_seconds: int = 3600  # 60 minutes
    ) -> str:
        """
        Generate a signed URL for downloading/viewing a video.

        Args:
            object_key: The object path in GCS
            expiration_seconds: URL expiration time in seconds

        Returns:
            Signed download URL
        """
        blob = self.bucket.blob(object_key)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration_seconds),
            method="GET",
        )

        return url

    def delete_object(self, object_key: str) -> bool:
        """
        Delete an object from GCS.

        Args:
            object_key: The object path to delete

        Returns:
            True if deleted successfully
        """
        try:
            blob = self.bucket.blob(object_key)
            blob.delete()
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
        blob = self.bucket.blob(object_key)
        return blob.exists()

    def get_object_metadata(self, object_key: str) -> Optional[dict]:
        """
        Get metadata for an object.

        Args:
            object_key: The object path

        Returns:
            Dict with metadata or None if not found
        """
        try:
            blob = self.bucket.blob(object_key)
            blob.reload()
            return {
                "key": object_key,
                "size": blob.size,
                "content_type": blob.content_type,
                "last_modified": blob.updated,
            }
        except Exception:
            return None
