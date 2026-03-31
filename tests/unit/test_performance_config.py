"""Tests for RAP-603: Performance optimization configuration."""

from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class TestNextConfigImageOptimization:
    """Verify image optimization settings in next.config.mjs."""

    def test_avif_format_configured(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "image/avif" in config_text

    def test_webp_format_configured(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "image/webp" in config_text

    def test_device_sizes_match_tailwind_breakpoints(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        for size in [640, 750, 828, 1080, 1200, 1920]:
            assert str(size) in config_text, f"Missing device size: {size}"

    def test_image_sizes_configured(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        for size in [16, 32, 48, 64, 96, 128, 256, 384]:
            assert str(size) in config_text, f"Missing image size: {size}"


class TestNextConfigCompression:
    """Verify compression and bundle optimization settings."""

    def test_gzip_compression_enabled(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "compress: true" in config_text

    def test_console_log_stripped_in_production(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "removeConsole" in config_text

    def test_console_error_warn_preserved(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert '"error"' in config_text
        assert '"warn"' in config_text


class TestNextConfigCacheHeaders:
    """Verify caching headers for static and image assets."""

    def test_static_assets_immutable_cache(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "public, max-age=31536000, immutable" in config_text

    def test_image_cache_with_stale_revalidate(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "stale-while-revalidate" in config_text

    def test_security_headers_nosniff(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "nosniff" in config_text

    def test_security_headers_deny_frame(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert "DENY" in config_text


class TestWebVitalsComponent:
    """Verify WebVitals component configuration."""

    def test_web_vitals_thresholds_lcp(self) -> None:
        component_text = (FRONTEND_DIR / "src" / "components" / "WebVitals.tsx").read_text()
        assert "LCP" in component_text
        assert "2500" in component_text
        assert "4000" in component_text

    def test_web_vitals_thresholds_cls(self) -> None:
        component_text = (FRONTEND_DIR / "src" / "components" / "WebVitals.tsx").read_text()
        assert "CLS" in component_text
        assert "0.1" in component_text
        assert "0.25" in component_text

    def test_web_vitals_thresholds_inp(self) -> None:
        component_text = (FRONTEND_DIR / "src" / "components" / "WebVitals.tsx").read_text()
        assert "INP" in component_text
        assert "200" in component_text
        assert "500" in component_text

    def test_web_vitals_registered_in_layout(self) -> None:
        layout_text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert 'import WebVitals from "@/components/WebVitals"' in layout_text
        assert "<WebVitals />" in layout_text

    def test_web_vitals_uses_send_beacon(self) -> None:
        component_text = (FRONTEND_DIR / "src" / "components" / "WebVitals.tsx").read_text()
        assert "sendBeacon" in component_text

    def test_web_vitals_dynamic_import(self) -> None:
        component_text = (FRONTEND_DIR / "src" / "components" / "WebVitals.tsx").read_text()
        assert 'import("web-vitals")' in component_text


class TestStandaloneOutput:
    """Verify standalone build output configuration."""

    def test_standalone_output_configured(self) -> None:
        config_text = (FRONTEND_DIR / "next.config.mjs").read_text()
        assert '"standalone"' in config_text
