"""Unit tests for storage backend service."""

from pathlib import Path
from unittest.mock import patch

import pytest
from src.services.storage_backend import (
    DEFAULT_LOCAL_PATH,
    DEFAULT_PRESIGN_EXPIRY_SECONDS,
    DEFAULT_STORAGE_BACKEND,
    ENV_MEDIA_LOCAL_PATH,
    ENV_S3_BUCKET,
    ENV_STORAGE_BACKEND,
    MAX_RETRY_ATTEMPTS,
    LocalStorage,
    StorageBackend,
    StorageError,
    StorageFactory,
)

# ---------------------------------------------------------------------------
# LocalStorage tests
# ---------------------------------------------------------------------------


class TestLocalStorage:
    """Tests for local filesystem storage."""

    @pytest.mark.asyncio
    async def test_upload_creates_file(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        source = tmp_path / "source.txt"
        source.write_text("hello")

        await storage.upload("uploads/test.txt", source)

        assert (tmp_path / "uploads" / "test.txt").exists()
        assert (tmp_path / "uploads" / "test.txt").read_text() == "hello"

    @pytest.mark.asyncio
    async def test_upload_creates_nested_dirs(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        source = tmp_path / "source.txt"
        source.write_text("data")

        await storage.upload("2026/03/27/uuid/file.webp", source)

        assert (tmp_path / "2026" / "03" / "27" / "uuid" / "file.webp").exists()

    @pytest.mark.asyncio
    async def test_download_copies_file(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        # Create a file in storage
        stored = tmp_path / "uploads" / "test.txt"
        stored.parent.mkdir(parents=True)
        stored.write_text("content")

        dest = tmp_path / "downloaded.txt"
        await storage.download("uploads/test.txt", dest)

        assert dest.read_text() == "content"

    @pytest.mark.asyncio
    async def test_download_missing_file_raises(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))

        with pytest.raises(StorageError, match="File not found"):
            await storage.download("nonexistent.txt", tmp_path / "out.txt")

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        target = tmp_path / "delete_me.txt"
        target.write_text("bye")

        await storage.delete("delete_me.txt")

        assert not target.exists()

    @pytest.mark.asyncio
    async def test_delete_missing_file_is_noop(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        # Should not raise
        await storage.delete("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_list_keys(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        (tmp_path / "prefix").mkdir()
        (tmp_path / "prefix" / "a.txt").write_text("a")
        (tmp_path / "prefix" / "b.txt").write_text("b")

        keys = await storage.list_keys("prefix")

        assert len(keys) == 2
        assert "prefix/a.txt" in keys
        assert "prefix/b.txt" in keys

    @pytest.mark.asyncio
    async def test_list_keys_empty_prefix(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))

        keys = await storage.list_keys("nonexistent")

        assert keys == []

    @pytest.mark.asyncio
    async def test_get_url_returns_local_path(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))

        url = await storage.get_url("uploads/2026/file.webp")

        assert "uploads/2026/file.webp" in url
        assert url.startswith("/")

    @pytest.mark.asyncio
    async def test_exists_returns_true(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        (tmp_path / "exists.txt").write_text("yes")

        assert await storage.exists("exists.txt") is True

    @pytest.mark.asyncio
    async def test_exists_returns_false(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))

        assert await storage.exists("nope.txt") is False

    def test_root_path_property(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        assert storage.root_path == tmp_path

    @pytest.mark.asyncio
    async def test_upload_error_raises_storage_error(self, tmp_path: Path) -> None:
        storage = LocalStorage(root_path=str(tmp_path))
        # Non-existent source file
        bad_source = tmp_path / "nonexistent_source.txt"

        with pytest.raises(StorageError, match="Failed to store"):
            await storage.upload("dest.txt", bad_source)


# ---------------------------------------------------------------------------
# StorageFactory tests
# ---------------------------------------------------------------------------


class TestStorageFactory:
    """Tests for the factory pattern."""

    def test_creates_local_by_default(self) -> None:
        backend = StorageFactory.create("local")
        assert isinstance(backend, LocalStorage)

    def test_unknown_backend_raises(self) -> None:
        with pytest.raises(StorageError, match="Unknown storage backend"):
            StorageFactory.create("ftp")

    @patch.dict("os.environ", {ENV_STORAGE_BACKEND: "local"})
    def test_reads_env_var(self) -> None:
        backend = StorageFactory.create()
        assert isinstance(backend, LocalStorage)

    def test_default_is_local(self) -> None:
        backend = StorageFactory.create()
        assert isinstance(backend, LocalStorage)


# ---------------------------------------------------------------------------
# StorageError tests
# ---------------------------------------------------------------------------


class TestStorageError:
    """Tests for the custom error."""

    def test_message_and_key(self) -> None:
        err = StorageError(message="fail", key="my/key")
        assert err.message == "fail"
        assert err.key == "my/key"
        assert str(err) == "fail"

    def test_key_optional(self) -> None:
        err = StorageError(message="no key")
        assert err.key is None


# ---------------------------------------------------------------------------
# StorageBackend ABC tests
# ---------------------------------------------------------------------------


class TestStorageBackendABC:
    """Verify the abstract base class cannot be instantiated."""

    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            StorageBackend()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_default_backend(self) -> None:
        assert DEFAULT_STORAGE_BACKEND == "local"

    def test_default_local_path(self) -> None:
        assert DEFAULT_LOCAL_PATH == "media"

    def test_default_presign_expiry(self) -> None:
        assert DEFAULT_PRESIGN_EXPIRY_SECONDS == 3600

    def test_max_retry_attempts(self) -> None:
        assert MAX_RETRY_ATTEMPTS == 3

    def test_env_var_names(self) -> None:
        assert ENV_STORAGE_BACKEND == "STORAGE_BACKEND"
        assert ENV_MEDIA_LOCAL_PATH == "MEDIA_LOCAL_PATH"
        assert ENV_S3_BUCKET == "AWS_S3_BUCKET"
