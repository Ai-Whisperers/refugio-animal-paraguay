"""Tests for RAP-597: Responsive design audit and fixes."""

from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


class TestResponsiveContainerComponent:
    """Verify ResponsiveContainer component exists and exports correctly."""

    def test_component_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").exists()

    def test_exports_responsive_container(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "export function ResponsiveContainer" in text

    def test_exports_responsive_grid(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "export function ResponsiveGrid" in text

    def test_exports_responsive_stack(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "export function ResponsiveStack" in text

    def test_exports_responsive_show(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "export function ResponsiveShow" in text

    def test_exports_responsive_image(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "export function ResponsiveImage" in text


class TestResponsiveContainerSizes:
    """Verify container size variants."""

    def test_size_sm(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"max-w-2xl"' in text

    def test_size_md(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"max-w-4xl"' in text

    def test_size_lg(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"max-w-6xl"' in text

    def test_size_xl(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"max-w-7xl"' in text

    def test_default_padding(self) -> None:
        """Default padding should follow px-4 sm:px-6 lg:px-8 pattern."""
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "px-4 sm:px-6 lg:px-8" in text


class TestResponsiveGridConfiguration:
    """Verify grid layout configuration."""

    def test_gap_sm(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"gap-3 sm:gap-4"' in text

    def test_gap_md(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"gap-4 sm:gap-6"' in text

    def test_gap_lg(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"gap-6 sm:gap-8"' in text

    def test_default_columns_mobile_first(self) -> None:
        """Default should start at 1 column on xs."""
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "grid-cols-1" in text


class TestResponsiveStackConfiguration:
    """Verify stack layout configuration."""

    def test_stack_direction_sm(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"flex-col sm:flex-row"' in text

    def test_stack_direction_md(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"flex-col md:flex-row"' in text

    def test_stack_alignment_options(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"items-start"' in text
        assert '"items-center"' in text
        assert '"items-end"' in text
        assert '"items-stretch"' in text


class TestResponsiveShowConfiguration:
    """Verify show/hide breakpoint configuration."""

    def test_above_sm(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"hidden sm:block"' in text

    def test_above_md(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"hidden md:block"' in text

    def test_below_sm(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"sm:hidden"' in text

    def test_below_md(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"md:hidden"' in text


class TestResponsiveImageConfiguration:
    """Verify responsive image aspect ratio support."""

    def test_aspect_square(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"aspect-square"' in text

    def test_aspect_video(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"aspect-video"' in text

    def test_aspect_4_3(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert '"aspect-[4/3]"' in text

    def test_overflow_hidden(self) -> None:
        """Images should clip overflow to maintain layout."""
        text = (FRONTEND_DIR / "src" / "components" / "ResponsiveContainer.tsx").read_text()
        assert "overflow-hidden" in text


class TestMobileFirstPatterns:
    """Verify mobile-first patterns in existing components."""

    def test_navbar_has_mobile_menu(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "Navbar.tsx").read_text()
        assert "md:hidden" in text
        assert "isMobileMenuOpen" in text

    def test_navbar_desktop_hidden_on_mobile(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "Navbar.tsx").read_text()
        assert "hidden md:flex" in text

    def test_footer_uses_responsive_padding(self) -> None:
        text = (FRONTEND_DIR / "src" / "components" / "Footer.tsx").read_text()
        assert "px-4" in text or "px-6" in text

    def test_layout_uses_min_h_screen(self) -> None:
        text = (FRONTEND_DIR / "src" / "app" / "layout.tsx").read_text()
        assert "min-h-screen" in text
