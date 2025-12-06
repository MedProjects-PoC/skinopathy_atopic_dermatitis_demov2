"""
Cloud Storage Service for uploading saliency maps and other assets
"""
from google.cloud import storage
from loguru import logger
from typing import Optional
import os
from app.core.config import settings


class CloudStorageService:
    """Service for interacting with Google Cloud Storage"""

    def __init__(self):
        self.client = None
        self.bucket = None
        self._initialize()

    def _initialize(self):
        """Initialize GCS client and bucket"""
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
            logger.info(f"Cloud Storage initialized: bucket={settings.GCS_BUCKET_NAME}")
        except Exception as e:
            logger.warning(f"Could not initialize Cloud Storage: {e}")
            self.client = None
            self.bucket = None

    def upload_saliency_map(
        self,
        local_path: str,
        session_id: str
    ) -> Optional[str]:
        """
        Upload saliency map to Cloud Storage

        Args:
            local_path: Local file path to upload
            session_id: Session ID for naming

        Returns:
            Public URL of uploaded file, or None if upload failed
        """
        if not self.bucket:
            logger.error("Cloud Storage not initialized")
            return None

        try:
            # Create blob name
            blob_name = f"{settings.GCS_SALIENCY_MAPS_PREFIX}{session_id}.png"
            blob = self.bucket.blob(blob_name)

            # Upload file
            blob.upload_from_filename(local_path, content_type='image/png')

            # Make public (or use signed URL for private access)
            blob.make_public()

            public_url = blob.public_url
            logger.success(f"Uploaded saliency map to GCS: {public_url}")

            return public_url

        except Exception as e:
            logger.error(f"Failed to upload saliency map to GCS: {e}")
            return None

    def get_signed_url(
        self,
        blob_name: str,
        expiration_minutes: int = 60
    ) -> Optional[str]:
        """
        Generate a signed URL for private access

        Args:
            blob_name: Name of the blob in GCS
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL, or None if generation failed
        """
        if not self.bucket:
            logger.error("Cloud Storage not initialized")
            return None

        try:
            from datetime import timedelta

            blob = self.bucket.blob(blob_name)
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )

            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None


# Global instance
cloud_storage_service = CloudStorageService()
