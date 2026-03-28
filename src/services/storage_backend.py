"""Abstract storage backend with local and S3 implementations.

Provides a pluggable storage interface for media files. Backend selection
is controlled by the STORAGE_BACKEND environment variable:
  - "local" (default): saves to local filesystem, served by Nginx
  - "s3": uses AWS S3 or compatible (MinIO, DigitalOcean Spaces)

Usage:
    backend = StorageFactory.create()
    await backend.upload("2026/03/27/uuid/file.webp", Path("/tmp/file.webp"))
    url = await backend.get_url("2026/03/27/uuid/file.webp")
"""

import logging
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)

# Environment variable names
ENV_STORAGE_BACKEND = "STORAGE_BACKEND"
ENV_MEDIA_LOCAL_PATH = "MEDIA_LOCAL_PATH"
ENV_S3_BUCKET = "AWS_S3_BUCKET"
ENV_S3_REGION = "AWS_S3_REGION"
ENV_S3_ENDPOINT = "AWS_S3_ENDPOINT"
ENV_S3_ACCESS_KEY = "AWS_ACCESS_KEY_ID"
ENV_S3_SECRET_KEY = "AWS_SECRET_ACCESS_KEY"

# Defaults
DEFAULT_STORAGE_BACKEND = "local"
DEFAULT_LOCAL_PATH = "media"
DEFAULT_PRESIGN_EXPIRY_SECONDS = 3600
MAX_RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 1.0


class StorageError(Exception):
    """Raised when a storage operation fails."""

    def __init__(self, message: str, key: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.key = key


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(self, key: str, file_path: Path) -> None:
        """Upload a file to storage.

        Parameters
        ----------
        key : str
            Storage key (relative path), e.g. "uploads/2026/03/27/uuid/file.webp"
        file_path : Path
            Local file path to upload from.
        """

    @abstractmethod
    async def download(self, key: str, destination: Path) -> None:
        """Download a file from storage.

        Parameters
        ----------
        key : str
            Storage key to download.
        destination : Path
            Local path to save the downloaded file.
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a file from storage."""

    @abstractmethod
    async def list_keys(self, prefix: str) -> list[str]:
        """List storage keys matching a prefix."""

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = DEFAULT_PRESIGN_EXPIRY_SECONDS) -> str:
        """Get a URL for accessing the stored file.

        For local storage, returns a path suitable for Nginx serving.
        For S3, returns a pre-signed URL with configurable expiry.
        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in storage."""


class LocalStorage(StorageBackend):
    """Local filesystem storage backend.

    Files are stored in a configurable root directory and served
    by Nginx (or similar) via path-based URLs.
    """

    def __init__(self, root_path: str | None = None) -> None:
        self._root = Path(root_path or os.getenv(ENV_MEDIA_LOCAL_PATH, DEFAULT_LOCAL_PATH))
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root_path(self) -> Path:
        """Return the storage root directory."""
        return self._root

    async def upload(self, key: str, file_path: Path) -> None:
        dest = self._root / key
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(file_path), str(dest))
        except OSError as exc:
            raise StorageError(
                message=f"Failed to store file locally: {exc}",
                key=key,
            ) from exc

        logger.debug("LocalStorage: uploaded %s", key)

    async def download(self, key: str, destination: Path) -> None:
        source = self._root / key
        if not source.exists():
            raise StorageError(
                message=f"File not found: {key}",
                key=key,
            )
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(destination))
        except OSError as exc:
            raise StorageError(
                message=f"Failed to download file: {exc}",
                key=key,
            ) from exc

    async def delete(self, key: str) -> None:
        target = self._root / key
        try:
            target.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError(
                message=f"Failed to delete file: {exc}",
                key=key,
            ) from exc

        logger.debug("LocalStorage: deleted %s", key)

    async def list_keys(self, prefix: str) -> list[str]:
        base = self._root / prefix
        if not base.exists():
            return []
        return [str(p.relative_to(self._root)) for p in base.rglob("*") if p.is_file()]

    async def get_url(self, key: str, expires_in: int = DEFAULT_PRESIGN_EXPIRY_SECONDS) -> str:
        # Local URLs are static paths — expiry is ignored
        return f"/{self._root}/{key}"

    async def exists(self, key: str) -> bool:
        return (self._root / key).exists()


class S3Storage(StorageBackend):
    """AWS S3 (or compatible) storage backend.

    Supports MinIO, DigitalOcean Spaces, and other S3-compatible services
    via custom endpoint configuration.
    """

    def __init__(
        self,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        import boto3
        from botocore.config import Config

        self._bucket = bucket or os.getenv(ENV_S3_BUCKET, "")
        self._region = region or os.getenv(ENV_S3_REGION, "us-east-1")
        self._endpoint = endpoint_url or os.getenv(ENV_S3_ENDPOINT)
        self._access_key = access_key or os.getenv(ENV_S3_ACCESS_KEY)
        self._secret_key = secret_key or os.getenv(ENV_S3_SECRET_KEY)

        if not self._bucket:
            raise StorageError(
                message="S3 bucket name is required (set AWS_S3_BUCKET env var)",
            )

        config = Config(
            retries={"max_attempts": MAX_RETRY_ATTEMPTS, "mode": "adaptive"},
        )

        kwargs: dict = {
            "service_name": "s3",
            "region_name": self._region,
            "config": config,
        }
        if self._endpoint:
            kwargs["endpoint_url"] = self._endpoint
        if self._access_key and self._secret_key:
            kwargs["aws_access_key_id"] = self._access_key
            kwargs["aws_secret_access_key"] = self._secret_key

        self._client = boto3.client(**kwargs)
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create the bucket if it doesn't exist."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except self._client.exceptions.ClientError:
            try:
                if self._region == "us-east-1":
                    self._client.create_bucket(Bucket=self._bucket)
                else:
                    self._client.create_bucket(
                        Bucket=self._bucket,
                        CreateBucketConfiguration={
                            "LocationConstraint": self._region,
                        },
                    )
                logger.info("S3Storage: created bucket %s", self._bucket)
            except Exception as exc:
                raise StorageError(
                    message=f"Failed to create S3 bucket: {exc}",
                ) from exc

    async def upload(self, key: str, file_path: Path) -> None:
        try:
            self._client.upload_file(str(file_path), self._bucket, key)
        except Exception as exc:
            raise StorageError(
                message=f"S3 upload failed: {exc}",
                key=key,
            ) from exc

        logger.debug("S3Storage: uploaded %s to %s", key, self._bucket)

    async def download(self, key: str, destination: Path) -> None:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            self._client.download_file(self._bucket, key, str(destination))
        except Exception as exc:
            raise StorageError(
                message=f"S3 download failed: {exc}",
                key=key,
            ) from exc

    async def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as exc:
            raise StorageError(
                message=f"S3 delete failed: {exc}",
                key=key,
            ) from exc

        logger.debug("S3Storage: deleted %s from %s", key, self._bucket)

    async def list_keys(self, prefix: str) -> list[str]:
        try:
            response = self._client.list_objects_v2(
                Bucket=self._bucket,
                Prefix=prefix,
            )
            return [obj["Key"] for obj in response.get("Contents", [])]
        except Exception as exc:
            raise StorageError(
                message=f"S3 list failed: {exc}",
                key=prefix,
            ) from exc

    async def get_url(self, key: str, expires_in: int = DEFAULT_PRESIGN_EXPIRY_SECONDS) -> str:
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        except Exception as exc:
            raise StorageError(
                message=f"Failed to generate pre-signed URL: {exc}",
                key=key,
            ) from exc

    async def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except self._client.exceptions.ClientError:
            return False


class StorageFactory:
    """Factory for creating storage backends based on configuration."""

    @staticmethod
    def create(backend_type: str | None = None) -> StorageBackend:
        """Create a storage backend instance.

        Parameters
        ----------
        backend_type : str | None
            "local" or "s3". Defaults to STORAGE_BACKEND env var or "local".
        """
        selected = backend_type or os.getenv(ENV_STORAGE_BACKEND, DEFAULT_STORAGE_BACKEND)

        if selected == "local":
            return LocalStorage()
        if selected == "s3":
            return S3Storage()

        raise StorageError(
            message=f"Unknown storage backend: {selected}. Must be 'local' or 's3'.",
        )
