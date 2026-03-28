"""Media file serving endpoint with cache headers and content negotiation.

In production, Nginx serves media files directly. This endpoint provides:
  - Development mode file serving
  - API fallback when Nginx is bypassed
  - Proper HTTP cache headers (Cache-Control, ETag, Last-Modified)
  - WebP content negotiation (serves .webp variant if available and accepted)

Endpoints:
  GET /media/{path:path}  -- serve a media file with CDN-appropriate headers
"""

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import FileResponse, Response

from src.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["media"])

# Cache-Control: 1 year, immutable (UUID filenames never change)
CACHE_MAX_AGE_SECONDS = 31_536_000
CACHE_CONTROL_VALUE = f"public, max-age={CACHE_MAX_AGE_SECONDS}, immutable"

# Allowed file extensions for serving (security: prevent path traversal to arbitrary files)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png", "webp", "gif", "svg", "pdf"})

# MIME types by extension
EXTENSION_TO_MIME: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
}

# Extensions eligible for WebP negotiation
WEBP_NEGOTIABLE_EXTENSIONS: frozenset[str] = frozenset({"jpg", "jpeg", "png"})


def _compute_etag(file_path: Path) -> str:
    """Compute ETag from file size and modification time.

    Uses size + mtime for speed — avoids reading entire file into memory.
    For UUID-named immutable files, this is sufficient.
    """
    stat = file_path.stat()
    raw = f"{stat.st_size}-{stat.st_mtime_ns}"
    return hashlib.md5(raw.encode()).hexdigest()


def _resolve_media_root() -> Path:
    """Resolve the media root directory from settings."""
    settings = get_settings()
    media_path = getattr(settings, "media_local_path", None)
    if media_path:
        return Path(media_path)
    return Path("media")


def _try_webp_negotiation(file_path: Path, accept_header: str | None) -> Path | None:
    """Check if a WebP variant exists and the client accepts it.

    Returns the WebP path if negotiation succeeds, None otherwise.
    """
    if accept_header is None:
        return None
    if "image/webp" not in accept_header:
        return None

    extension = file_path.suffix.lower().lstrip(".")
    if extension not in WEBP_NEGOTIABLE_EXTENSIONS:
        return None

    webp_path = file_path.with_suffix(".webp")
    if webp_path.exists() and webp_path.is_file():
        return webp_path

    return None


@router.get(
    "/media/{file_path:path}",
    summary="Serve a media file",
    description=(
        "Serve a media file with proper cache headers. "
        "In production, Nginx handles this directly."
    ),
    responses={
        200: {"description": "File served with cache headers"},
        304: {"description": "Not Modified (ETag match)"},
        403: {"description": "File type not allowed"},
        404: {"description": "File not found"},
    },
)
async def serve_media_file(
    file_path: str,
    if_none_match: str | None = Header(default=None),
    accept: str | None = Header(default=None),
) -> Response:
    """Serve a media file with CDN-appropriate cache headers.

    Supports:
    - Cache-Control with immutable directive
    - ETag-based conditional requests (If-None-Match -> 304)
    - WebP content negotiation for image files
    - Security: only serves allowed file extensions
    """
    # Security: validate extension
    extension = Path(file_path).suffix.lower().lstrip(".")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "File type not allowed"},
        )

    # Security: prevent path traversal
    if ".." in file_path or file_path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Invalid path"},
        )

    media_root = _resolve_media_root()
    absolute_path = (media_root / file_path).resolve()

    # Ensure resolved path is still under media root
    try:
        absolute_path.relative_to(media_root.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Invalid path"},
        ) from None

    if not absolute_path.exists() or not absolute_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "File not found"},
        )

    # WebP content negotiation
    serve_path = absolute_path
    webp_path = _try_webp_negotiation(absolute_path, accept)
    if webp_path is not None:
        serve_path = webp_path

    # Compute ETag
    etag = _compute_etag(serve_path)
    etag_header = f'"{etag}"'

    # Conditional request: return 304 if ETag matches
    if if_none_match and if_none_match.strip('" ') == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={
                "ETag": etag_header,
                "Cache-Control": CACHE_CONTROL_VALUE,
            },
        )

    # Determine content type
    serve_extension = serve_path.suffix.lower().lstrip(".")
    content_type = EXTENSION_TO_MIME.get(serve_extension, "application/octet-stream")

    # Last-Modified from file mtime
    stat = serve_path.stat()
    last_modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
    last_modified_str = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")

    return FileResponse(
        path=str(serve_path),
        media_type=content_type,
        headers={
            "Cache-Control": CACHE_CONTROL_VALUE,
            "ETag": etag_header,
            "Last-Modified": last_modified_str,
            "X-Content-Type-Options": "nosniff",
            "Access-Control-Allow-Origin": "*",
            "Vary": "Accept, Accept-Encoding",
        },
    )
