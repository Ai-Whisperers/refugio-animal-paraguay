"""Tests for RAP-602: App-like bottom navigation bar."""

from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class TestBottomNavComponent:
    """Verify BottomNav component structure and configuration."""

    def test_component_exists(self) -> None:
        component_path = FRONTEND_DIR / "src" / "components" / "BottomNav.tsx"
        assert component_path.exists()

    def test_is_client_component(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert '"use client"' in text

    def test_has_home_link(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'href: "/"' in text

    def test_has_animals_link(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'href: "/animals"' in text

    def test_has_donate_link(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'href: "/donate"' in text

    def test_has_stories_link(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'href: "/stories"' in text

    def test_hidden_on_desktop(self) -> None:
        """Bottom nav should be hidden on md+ screens."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert "md:hidden" in text

    def test_hidden_on_admin_pages(self) -> None:
        """Bottom nav should not render on admin pages."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert '"/admin"' in text
        assert "return null" in text

    def test_minimum_touch_target(self) -> None:
        """Touch targets should be at least 44px per WCAG 2.1."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert "min-h-[44px]" in text

    def test_more_menu_exists(self) -> None:
        """More button should exist for additional navigation items."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert "isMoreOpen" in text
        assert "Mas" in text

    def test_more_menu_has_about_and_contact(self) -> None:
        """More menu should contain About and Contact links."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'href: "/about"' in text
        assert 'href: "/contact"' in text

    def test_aria_navigation_label(self) -> None:
        """Nav element should have an aria-label in Spanish."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'aria-label="Navegacion principal"' in text

    def test_aria_current_page(self) -> None:
        """Active link should have aria-current=page."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert 'aria-current={active ? "page" : undefined}' in text

    def test_content_spacer_exists(self) -> None:
        """A spacer div should prevent content from hiding behind the fixed nav."""
        text = (FRONTEND_DIR / "src" / "components" / "BottomNav.tsx").read_text()
        assert "h-16" in text
        assert 'aria-hidden="true"' in text


class TestBottomNavIntegration:
    """Verify BottomNav is registered in the root layout."""

    def test_imported_in_layout(self) -> None:
        layout_text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert 'import BottomNav from "@/components/BottomNav"' in layout_text

    def test_rendered_in_layout(self) -> None:
        layout_text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert "<BottomNav />" in layout_text
