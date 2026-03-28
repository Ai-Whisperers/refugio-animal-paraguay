"""Tests for RAP-603: Performance optimization configuration."""

import pytest


# --- next.config.mjs validation ---


class TestNextConfigImageOptimization:
    """Verify image optimization settings in next.config.mjs."""

    def test_avif_format_configured(self) -> None:
        """AVIF should be listed as preferred image format."""
        import json
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "image/avif" in config_text

    def test_webp_format_configured(self) -> None:
        """WebP should be listed as fallback image format."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "image/webp" in config_text

    def test_device_sizes_match_tailwind_breakpoints(self) -> None:
        """Device sizes should cover common responsive breakpoints."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        for size in [640, 750, 828, 1080, 1200, 1920]:
            assert str(size) in config_text, f"Missing device size: {size}"

    def test_image_sizes_configured(self) -> None:
        """Small image sizes should be configured for icons/thumbnails."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        for size in [16, 32, 48, 64, 96, 128, 256, 384]:
            assert str(size) in config_text, f"Missing image size: {size}"


class TestNextConfigCompression:
    """Verify compression and bundle optimization settings."""

    def test_gzip_compression_enabled(self) -> None:
        """Gzip compression should be enabled."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "compress: true" in config_text

    def test_console_log_stripped_in_production(self) -> None:
        """Console.log should be removed in production builds."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "removeConsole" in config_text

    def test_console_error_warn_preserved(self) -> None:
        """Console.error and console.warn should be kept in production."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert '"error"' in config_text
        assert '"warn"' in config_text


class TestNextConfigCacheHeaders:
    """Verify caching headers for static and image assets."""

    def test_static_assets_immutable_cache(self) -> None:
        """Static assets should have immutable 1-year cache."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "public, max-age=31536000, immutable" in config_text

    def test_image_cache_with_stale_revalidate(self) -> None:
        """Optimized images should have stale-while-revalidate caching."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "stale-while-revalidate" in config_text

    def test_security_headers_nosniff(self) -> None:
        """X-Content-Type-Options: nosniff should be set."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "nosniff" in config_text

    def test_security_headers_deny_frame(self) -> None:
        """X-Frame-Options: DENY should be set."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert "DENY" in config_text


class TestWebVitalsComponent:
    """Verify WebVitals component configuration."""

    def test_web_vitals_thresholds_lcp(self) -> None:
        """LCP threshold should follow Google standards (2500ms good, 4000ms poor)."""
        from pathlib import Path

        component_text = Path("frontend/src/components/WebVitals.tsx").read_text()
        assert "LCP" in component_text
        assert "2500" in component_text
        assert "4000" in component_text

    def test_web_vitals_thresholds_cls(self) -> None:
        """CLS threshold should follow Google standards (0.1 good, 0.25 poor)."""
        from pathlib import Path

        component_text = Path("frontend/src/components/WebVitals.tsx").read_text()
        assert "CLS" in component_text
        assert "0.1" in component_text
        assert "0.25" in component_text

    def test_web_vitals_thresholds_inp(self) -> None:
        """INP threshold should follow Google standards (200ms good, 500ms poor)."""
        from pathlib import Path

        component_text = Path("frontend/src/components/WebVitals.tsx").read_text()
        assert "INP" in component_text
        assert "200" in component_text
        assert "500" in component_text

    def test_web_vitals_registered_in_layout(self) -> None:
        """WebVitals component should be imported and rendered in root layout."""
        from pathlib import Path

        layout_text = Path("frontend/src/app/layout.tsx").read_text()
        assert 'import WebVitals from "@/components/WebVitals"' in layout_text
        assert "<WebVitals />" in layout_text

    def test_web_vitals_uses_send_beacon(self) -> None:
        """Production reporting should use sendBeacon for reliable delivery."""
        from pathlib import Path

        component_text = Path("frontend/src/components/WebVitals.tsx").read_text()
        assert "sendBeacon" in component_text

    def test_web_vitals_dynamic_import(self) -> None:
        """web-vitals library should be dynamically imported to avoid blocking."""
        from pathlib import Path

        component_text = Path("frontend/src/components/WebVitals.tsx").read_text()
        assert 'import("web-vitals")' in component_text


class TestStandaloneOutput:
    """Verify standalone build output configuration."""

    def test_standalone_output_configured(self) -> None:
        """Next.js should output as standalone for Docker deployment."""
        from pathlib import Path

        config_text = Path("frontend/next.config.mjs").read_text()
        assert '"standalone"' in config_text
