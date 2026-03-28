"""Tests for video embed support (RAP-630)."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Component structure tests
# ---------------------------------------------------------------------------


class TestVideoEmbedComponent:
    """Verify VideoEmbed component exists and is properly structured."""

    def test_file_exists(self) -> None:
        assert Path("frontend/src/components/VideoEmbed.tsx").exists()

    def test_exports_default_component(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "export default function VideoEmbed" in content

    def test_exports_video_gallery(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "export function VideoGallery" in content

    def test_exports_parse_function(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "export function parseVideoUrl" in content

    def test_exports_types(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "export interface VideoEmbedProps" in content
        assert "export interface VideoItem" in content

    def test_is_client_component(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert '"use client"' in content


# ---------------------------------------------------------------------------
# YouTube support tests
# ---------------------------------------------------------------------------


class TestYouTubeSupport:
    """Test YouTube video parsing and embedding."""

    def test_component_has_youtube_regex(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "YOUTUBE_REGEX" in content

    def test_parses_standard_youtube_url(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "youtube.com" in content
        assert "youtu" in content and "be" in content

    def test_generates_youtube_embed_url(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "youtube.com/embed/" in content

    def test_has_youtube_thumbnail(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "img.youtube.com" in content
        assert "maxresdefault" in content

    def test_has_lazy_load_thumbnail(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "isLoaded" in content
        assert "setIsLoaded" in content


# ---------------------------------------------------------------------------
# Vimeo support tests
# ---------------------------------------------------------------------------


class TestVimeoSupport:
    """Test Vimeo video parsing."""

    def test_component_has_vimeo_regex(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "VIMEO_REGEX" in content

    def test_generates_vimeo_embed_url(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "player.vimeo.com/video/" in content


# ---------------------------------------------------------------------------
# Provider badge tests
# ---------------------------------------------------------------------------


class TestProviderBadge:
    """Test provider badge component."""

    def test_has_provider_badge(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "ProviderBadge" in content

    def test_has_youtube_label(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert '"YouTube"' in content

    def test_has_vimeo_label(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert '"Vimeo"' in content


# ---------------------------------------------------------------------------
# iframe embed tests
# ---------------------------------------------------------------------------


class TestIframeEmbed:
    """Test iframe rendering."""

    def test_has_iframe(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "<iframe" in content

    def test_iframe_has_title(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "title={title}" in content

    def test_iframe_has_allow_fullscreen(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "allowFullScreen" in content

    def test_iframe_lazy_loads(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert 'loading="lazy"' in content

    def test_has_aspect_ratio(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "aspectRatio" in content

    def test_default_aspect_ratio(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert '"16/9"' in content


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test error handling for invalid URLs."""

    def test_handles_unsupported_url(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "URL de video no soportada" in content

    def test_has_error_state(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "hasError" in content
        assert "Error al cargar el video" in content


# ---------------------------------------------------------------------------
# Video Gallery tests
# ---------------------------------------------------------------------------


class TestVideoGallery:
    """Test VideoGallery component."""

    def test_has_category_filter(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "filter" in content
        assert "setFilter" in content

    def test_has_all_category(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert '"Todos"' in content

    def test_supports_column_config(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "columns" in content
        assert "grid-cols-1" in content

    def test_has_empty_state(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "No hay videos" in content


# ---------------------------------------------------------------------------
# Educational videos page tests
# ---------------------------------------------------------------------------


class TestEducationalVideosPage:
    """Test the educational videos page."""

    def test_file_exists(self) -> None:
        assert Path("frontend/src/app/educacion/videos/page.tsx").exists()

    def test_is_client_component(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert '"use client"' in content

    def test_has_page_title(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert "Videos educativos" in content

    def test_imports_video_gallery(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert "VideoGallery" in content

    def test_has_sample_videos(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert "EDUCATIONAL_VIDEOS" in content

    def test_has_categories(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert "Cuidado animal" in content
        assert "Esterilizacion" in content
        assert "Salud" in content
        assert "Adopcion" in content

    def test_has_suggest_section(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert "sugerir un video" in content

    def test_has_video_descriptions(self) -> None:
        content = Path("frontend/src/app/educacion/videos/page.tsx").read_text()
        assert "description" in content


# ---------------------------------------------------------------------------
# Accessibility tests
# ---------------------------------------------------------------------------


class TestVideoEmbedAccessibility:
    """Test accessibility features."""

    def test_aria_labels(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "aria-label" in content

    def test_role_alert_for_errors(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert 'role="alert"' in content

    def test_role_list_for_gallery(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert 'role="list"' in content
        assert 'role="listitem"' in content

    def test_aria_pressed_for_filters(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "aria-pressed" in content

    def test_touch_targets(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "min-h-[44px]" in content

    def test_img_alt_text(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "alt=" in content

    def test_play_button_has_label(self) -> None:
        content = Path("frontend/src/components/VideoEmbed.tsx").read_text()
        assert "Reproducir video" in content
