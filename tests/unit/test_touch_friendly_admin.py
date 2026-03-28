"""Tests for RAP-601: Touch-friendly admin interface."""

from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class TestTouchTargetComponent:
    """Verify TouchTarget component and utilities."""

    def test_component_exists(self) -> None:
        path = FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx"
        assert path.exists()

    def test_is_client_component(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert '"use client"' in text

    def test_minimum_44px_touch_target(self) -> None:
        """WCAG 2.1 SC 2.5.5 requires 44x44px minimum touch targets."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "min-h-[44px]" in text
        assert "min-w-[44px]" in text

    def test_touch_classes_target(self) -> None:
        """TOUCH_CLASSES.target should define min touch dimensions."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "TOUCH_CLASSES" in text
        assert 'target: "min-h-[44px] min-w-[44px]"' in text

    def test_touch_classes_button(self) -> None:
        """TOUCH_CLASSES.button should have responsive sizing."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "button:" in text
        assert "min-h-[44px]" in text

    def test_touch_classes_input(self) -> None:
        """TOUCH_CLASSES.input should have larger height on mobile."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "input:" in text
        assert "h-12" in text

    def test_touch_scroll_table_exists(self) -> None:
        """TouchScrollTable should enable horizontal scrolling."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "TouchScrollTable" in text
        assert "overflow-x-auto" in text
        assert "touch-pan-x" in text

    def test_pull_to_refresh_indicator(self) -> None:
        """PullToRefreshIndicator should show loading state."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "PullToRefreshIndicator" in text
        assert "isRefreshing" in text
        assert "animate-spin" in text

    def test_forward_ref_support(self) -> None:
        """TouchTarget should support refs via forwardRef."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert "forwardRef" in text

    def test_display_name_set(self) -> None:
        """forwardRef component should set displayName for DevTools."""
        text = (FRONTEND_DIR / "src" / "components" / "admin" / "TouchTarget.tsx").read_text()
        assert 'displayName = "TouchTarget"' in text


class TestTouchFriendlyCSS:
    """Verify touch-friendly CSS additions."""

    def test_touch_scroll_class(self) -> None:
        """touch-scroll utility class should exist."""
        css_text = (FRONTEND_DIR / "src" / "app" / "globals.css").read_text()
        assert ".touch-scroll" in css_text
        assert "-webkit-overflow-scrolling: touch" in css_text

    def test_safe_area_padding(self) -> None:
        """pb-safe class for notched devices should exist."""
        css_text = (FRONTEND_DIR / "src" / "app" / "globals.css").read_text()
        assert ".pb-safe" in css_text
        assert "safe-area-inset-bottom" in css_text

    def test_touch_action_manipulation(self) -> None:
        """touch-action-manipulation class should exist."""
        css_text = (FRONTEND_DIR / "src" / "app" / "globals.css").read_text()
        assert ".touch-action-manipulation" in css_text
        assert "touch-action: manipulation" in css_text


class TestAdminLayoutTouchFriendly:
    """Verify admin layout supports touch interactions."""

    def test_admin_layout_has_padding(self) -> None:
        """Admin main content should have mobile-friendly padding."""
        layout_text = (FRONTEND_DIR / "src" / "app" / "admin" / "layout.tsx").read_text()
        assert "px-4" in layout_text

    def test_admin_sidebar_mobile_support(self) -> None:
        """Admin sidebar should have mobile hamburger menu."""
        sidebar_text = (FRONTEND_DIR / "src" / "components" / "admin" / "AdminSidebar.tsx").read_text()
        assert "md:hidden" in sidebar_text
        assert "isMobileOpen" in sidebar_text
