"""Tests for RAP-596: PWA manifest and service worker setup."""

import json
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class TestPWAManifest:
    """Verify PWA manifest configuration."""

    def test_manifest_exists(self) -> None:
        assert (FRONTEND_DIR / "public" / "manifest.json").exists()

    def test_manifest_is_valid_json(self) -> None:
        text = (FRONTEND_DIR / "public" / "manifest.json").read_text()
        manifest = json.loads(text)
        assert isinstance(manifest, dict)

    def test_manifest_name(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["name"] == "Refugio Animal Paraguay"

    def test_manifest_short_name(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["short_name"] == "Refugio Animal"

    def test_manifest_display_standalone(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["display"] == "standalone"

    def test_manifest_theme_color(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["theme_color"] == "#E8622A"

    def test_manifest_background_color(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["background_color"] == "#FAFAF8"

    def test_manifest_start_url(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["start_url"] == "/"

    def test_manifest_language(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["lang"] == "es-PY"

    def test_manifest_has_icons(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert len(manifest["icons"]) >= 2

    def test_manifest_icon_sizes(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        sizes = [icon["sizes"] for icon in manifest["icons"]]
        assert "192x192" in sizes
        assert "512x512" in sizes

    def test_manifest_has_shortcuts(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert len(manifest["shortcuts"]) >= 2
        urls = [s["url"] for s in manifest["shortcuts"]]
        assert "/animals" in urls
        assert "/donate" in urls

    def test_manifest_orientation(self) -> None:
        manifest = json.loads((FRONTEND_DIR / "public" / "manifest.json").read_text())
        assert manifest["orientation"] == "portrait-primary"


class TestServiceWorker:
    """Verify service worker configuration."""

    def test_sw_exists(self) -> None:
        assert (FRONTEND_DIR / "public" / "sw.js").exists()

    def test_sw_has_cache_name(self) -> None:
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert "CACHE_NAME" in text
        assert "refugio-animal-v1" in text

    def test_sw_has_install_handler(self) -> None:
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert '"install"' in text
        assert "PRECACHE_ASSETS" in text

    def test_sw_has_activate_handler(self) -> None:
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert '"activate"' in text
        assert "caches.delete" in text

    def test_sw_has_fetch_handler(self) -> None:
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert '"fetch"' in text

    def test_sw_skips_api_calls(self) -> None:
        """API calls should not be cached by the service worker."""
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert '"/api/"' in text

    def test_sw_network_first_strategy(self) -> None:
        """Service worker should use network-first, cache fallback strategy."""
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert "fetch(event.request)" in text
        assert "caches.match(event.request)" in text

    def test_sw_offline_fallback(self) -> None:
        """Should fallback to offline page for navigation requests."""
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert "OFFLINE_URL" in text
        assert '"/offline"' in text

    def test_sw_skip_waiting(self) -> None:
        """Service worker should activate immediately on install."""
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert "self.skipWaiting()" in text

    def test_sw_clients_claim(self) -> None:
        """Service worker should take control of clients immediately."""
        text = (FRONTEND_DIR / "public" / "sw.js").read_text()
        assert "self.clients.claim()" in text


class TestServiceWorkerRegistration:
    """Verify SW registration component."""

    def test_registration_component_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "components" / "ServiceWorkerRegistration.tsx").exists()

    def test_registration_is_client_component(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ServiceWorkerRegistration.tsx").read_text()
        assert '"use client"' in text

    def test_registration_checks_support(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ServiceWorkerRegistration.tsx").read_text()
        assert '"serviceWorker" in navigator' in text

    def test_registration_registers_sw(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ServiceWorkerRegistration.tsx").read_text()
        assert 'register("/sw.js")' in text

    def test_registration_handles_updates(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ServiceWorkerRegistration.tsx").read_text()
        assert "updatefound" in text
        assert "registration.update()" in text

    def test_registered_in_layout(self) -> None:
        layout_text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert "ServiceWorkerRegistration" in layout_text
        assert "<ServiceWorkerRegistration />" in layout_text


class TestOfflinePage:
    """Verify offline fallback page."""

    def test_offline_page_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "app" / "offline" / "page.tsx").exists()

    def test_offline_page_has_retry_button(self) -> None:
        text = (FRONTEND_DIR / "src" / "app" / "offline" / "page.tsx").read_text()
        assert "Reintentar" in text
        assert "window.location.reload()" in text

    def test_offline_page_spanish_content(self) -> None:
        text = (FRONTEND_DIR / "src" / "app" / "offline" / "page.tsx").read_text()
        assert "Sin conexion" in text


class TestLayoutPWAMetadata:
    """Verify PWA metadata in root layout."""

    def test_manifest_link_in_metadata(self) -> None:
        layout_text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert '"/manifest.json"' in layout_text

    def test_apple_web_app_capable(self) -> None:
        layout_text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert "appleWebApp" in layout_text
        assert "capable: true" in layout_text
