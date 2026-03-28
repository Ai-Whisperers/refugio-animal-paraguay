"""Unit tests for media file serving with cache headers and content negotiation."""

import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from src.api.media_serve import (
    ALLOWED_EXTENSIONS,
    CACHE_CONTROL_VALUE,
    CACHE_MAX_AGE_SECONDS,
    EXTENSION_TO_MIME,
    WEBP_NEGOTIABLE_EXTENSIONS,
    _compute_etag,
    _try_webp_negotiation,
)

# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify media serving constants."""

    def test_cache_max_age_is_one_year(self) -> None:
        assert CACHE_MAX_AGE_SECONDS == 31_536_000

    def test_cache_control_value(self) -> None:
        assert "public" in CACHE_CONTROL_VALUE
        assert "immutable" in CACHE_CONTROL_VALUE
        assert "31536000" in CACHE_CONTROL_VALUE

    def test_allowed_extensions(self) -> None:
        assert "jpg" in ALLOWED_EXTENSIONS
        assert "jpeg" in ALLOWED_EXTENSIONS
        assert "png" in ALLOWED_EXTENSIONS
        assert "webp" in ALLOWED_EXTENSIONS
        assert "pdf" in ALLOWED_EXTENSIONS
        assert "svg" in ALLOWED_EXTENSIONS
        assert "gif" in ALLOWED_EXTENSIONS
        assert "exe" not in ALLOWED_EXTENSIONS

    def test_mime_types_mapping(self) -> None:
        assert EXTENSION_TO_MIME["jpg"] == "image/jpeg"
        assert EXTENSION_TO_MIME["png"] == "image/png"
        assert EXTENSION_TO_MIME["webp"] == "image/webp"
        assert EXTENSION_TO_MIME["pdf"] == "application/pdf"
        assert EXTENSION_TO_MIME["svg"] == "image/svg+xml"

    def test_webp_negotiable_extensions(self) -> None:
        assert "jpg" in WEBP_NEGOTIABLE_EXTENSIONS
        assert "jpeg" in WEBP_NEGOTIABLE_EXTENSIONS
        assert "png" in WEBP_NEGOTIABLE_EXTENSIONS
        assert "webp" not in WEBP_NEGOTIABLE_EXTENSIONS
        assert "pdf" not in WEBP_NEGOTIABLE_EXTENSIONS


# ---------------------------------------------------------------------------
# _compute_etag tests
# ---------------------------------------------------------------------------


class TestComputeEtag:
    """Tests for ETag computation from file metadata."""

    def test_returns_string(self, tmp_path: Path) -> None:
        f = tmp_path / "test.jpg"
        f.write_bytes(b"image data")
        etag = _compute_etag(f)
        assert isinstance(etag, str)
        assert len(etag) == 32  # MD5 hex digest

    def test_consistent_for_same_file(self, tmp_path: Path) -> None:
        f = tmp_path / "test.jpg"
        f.write_bytes(b"image data")
        assert _compute_etag(f) == _compute_etag(f)

    def test_different_for_different_content(self, tmp_path: Path) -> None:
        f1 = tmp_path / "a.jpg"
        f2 = tmp_path / "b.jpg"
        f1.write_bytes(b"image data 1")
        f2.write_bytes(b"image data 2")
        # Different size -> different etag
        assert _compute_etag(f1) != _compute_etag(f2)

    def test_uses_size_and_mtime(self, tmp_path: Path) -> None:
        f = tmp_path / "test.jpg"
        f.write_bytes(b"data")
        stat = f.stat()
        expected_raw = f"{stat.st_size}-{stat.st_mtime_ns}"
        expected = hashlib.md5(expected_raw.encode()).hexdigest()
        assert _compute_etag(f) == expected


# ---------------------------------------------------------------------------
# _try_webp_negotiation tests
# ---------------------------------------------------------------------------


class TestWebpNegotiation:
    """Tests for WebP content negotiation."""

    def test_returns_none_when_no_accept_header(self, tmp_path: Path) -> None:
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"jpeg data")
        assert _try_webp_negotiation(f, None) is None

    def test_returns_none_when_webp_not_accepted(self, tmp_path: Path) -> None:
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"jpeg data")
        assert _try_webp_negotiation(f, "image/jpeg, image/png") is None

    def test_returns_none_when_no_webp_file(self, tmp_path: Path) -> None:
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"jpeg data")
        # No .webp variant exists
        assert _try_webp_negotiation(f, "image/webp, image/jpeg") is None

    def test_returns_webp_path_when_available(self, tmp_path: Path) -> None:
        f = tmp_path / "photo.jpg"
        f.write_bytes(b"jpeg data")
        webp = tmp_path / "photo.webp"
        webp.write_bytes(b"webp data")
        result = _try_webp_negotiation(f, "image/webp, image/jpeg")
        assert result == webp

    def test_returns_none_for_non_negotiable_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"pdf data")
        webp = tmp_path / "doc.webp"
        webp.write_bytes(b"webp data")
        assert _try_webp_negotiation(f, "image/webp") is None

    def test_png_is_negotiable(self, tmp_path: Path) -> None:
        f = tmp_path / "image.png"
        f.write_bytes(b"png data")
        webp = tmp_path / "image.webp"
        webp.write_bytes(b"webp data")
        result = _try_webp_negotiation(f, "image/webp,*/*")
        assert result == webp


# ---------------------------------------------------------------------------
# Endpoint tests (via TestClient)
# ---------------------------------------------------------------------------


class TestServeMediaEndpoint:
    """Integration tests for the /media/ endpoint."""

    @pytest.fixture()
    def media_dir(self, tmp_path: Path) -> Path:
        """Create a temporary media directory with test files."""
        media = tmp_path / "media"
        media.mkdir()
        # Create a test image
        (media / "uploads").mkdir()
        img = media / "uploads" / "test-uuid.jpg"
        img.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # JPEG header
        # Create a WebP variant
        webp = media / "uploads" / "test-uuid.webp"
        webp.write_bytes(b"RIFF" + b"\x00" * 100)  # WebP header
        # Create a PDF
        pdf = media / "uploads" / "doc-uuid.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        return media

    @pytest.fixture()
    def client(self, media_dir: Path):
        """Create test client with media root patched."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.api.media_serve import router

        app = FastAPI()
        app.include_router(router)

        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            yield TestClient(app)

    def test_serve_jpeg(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            response = client.get("/media/uploads/test-uuid.jpg")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == CACHE_CONTROL_VALUE
        assert "ETag" in response.headers
        assert "Last-Modified" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "Accept" in response.headers["Vary"]

    def test_serve_pdf(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            response = client.get("/media/uploads/doc-uuid.pdf")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == CACHE_CONTROL_VALUE

    def test_304_not_modified(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            # First request to get ETag
            r1 = client.get("/media/uploads/test-uuid.jpg")
            etag = r1.headers["ETag"]

            # Second request with If-None-Match
            r2 = client.get(
                "/media/uploads/test-uuid.jpg",
                headers={"If-None-Match": etag},
            )
        assert r2.status_code == 304

    def test_webp_negotiation(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            response = client.get(
                "/media/uploads/test-uuid.jpg",
                headers={"Accept": "image/webp,image/jpeg,*/*"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/webp"

    def test_no_webp_without_accept(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            response = client.get(
                "/media/uploads/test-uuid.jpg",
                headers={"Accept": "image/jpeg"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    def test_forbidden_extension(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            response = client.get("/media/uploads/malware.exe")
        assert response.status_code == 403

    def test_path_traversal_blocked(self, client, media_dir: Path) -> None:
        """Path traversal is blocked — FastAPI normalizes .. segments,
        and our resolve() + relative_to() check catches the rest."""
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            # FastAPI normalizes ../.. so the file won't exist under media root
            response = client.get("/media/../../../etc/passwd.pdf")
        assert response.status_code in (403, 404)

    def test_file_not_found(self, client, media_dir: Path) -> None:
        with patch("src.api.media_serve._resolve_media_root", return_value=media_dir):
            response = client.get("/media/nonexistent.jpg")
        assert response.status_code == 404
