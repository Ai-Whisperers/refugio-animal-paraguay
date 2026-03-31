"""Tests for education hub public page (RAP-626)."""

from __future__ import annotations

from pathlib import Path


class TestPageStructure:
    """Verify page exists and has correct structure."""

    def test_file_exists(self) -> None:
        assert Path("frontend/src/app/educacion/page.tsx").exists()

    def test_is_client_component(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert '"use client"' in content

    def test_exports_default_page(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "export default function EducationHubPage" in content


class TestHeader:
    """Test page header and title."""

    def test_has_page_title(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "Centro Educativo" in content

    def test_has_description(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "Recursos y articulos" in content


class TestFeaturedSections:
    """Test featured section cards."""

    def test_has_featured_sections(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "FeaturedSectionCard" in content
        assert "FEATURED_SECTIONS" in content

    def test_links_to_sterilization(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "/educacion/esterilizacion" in content

    def test_links_to_videos(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "/educacion/videos" in content


class TestSearchAndFilter:
    """Test search and category filter components."""

    def test_has_search_bar(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "SearchBar" in content
        assert "Buscar articulos" in content

    def test_has_category_filter(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "CategoryFilter" in content

    def test_has_all_categories(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert '"Todos"' in content
        assert '"Cuidado animal"' in content
        assert '"Salud"' in content
        assert '"Adopcion"' in content
        assert '"Esterilizacion"' in content
        assert '"Nutricion"' in content
        assert '"Comportamiento"' in content

    def test_search_filters_by_text(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "searchTerm" in content
        assert "toLowerCase" in content


class TestArticleCards:
    """Test article card component."""

    def test_has_article_card(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "ArticleCard" in content

    def test_shows_category_badge(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "categoryLabel" in content

    def test_shows_read_time(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "read_time_minutes" in content
        assert "min de lectura" in content

    def test_has_read_more_link(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "Leer mas" in content

    def test_links_to_article_detail(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "/educacion/articulos/" in content

    def test_shows_publish_date(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "published_at" in content
        assert "toLocaleDateString" in content


class TestSampleArticles:
    """Test sample articles data."""

    def test_has_sample_articles(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "SAMPLE_ARTICLES" in content

    def test_has_six_articles(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "art-1" in content
        assert "art-6" in content

    def test_articles_cover_categories(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert '"adopcion"' in content
        assert '"salud"' in content
        assert '"nutricion"' in content
        assert '"cuidado"' in content
        assert '"comportamiento"' in content


class TestAPIIntegration:
    """Test API integration."""

    def test_fetches_from_api(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "/api/articles/public" in content

    def test_falls_back_to_sample(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "SAMPLE_ARTICLES" in content
        assert "fallback" in content.lower() or "sample" in content.lower()


class TestEmptyAndLoadingStates:
    """Test empty and loading states."""

    def test_has_loading_skeleton(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "LoadingSkeleton" in content
        assert "animate-pulse" in content

    def test_has_empty_state(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "EmptyState" in content
        assert "No se encontraron articulos" in content

    def test_shows_article_count(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "articulo" in content
        assert "encontrado" in content


class TestNewsletterCTA:
    """Test newsletter/CTA section."""

    def test_has_cta_section(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "Mantente informado" in content

    def test_has_contact_link(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "Contactanos" in content


class TestAccessibility:
    """Test accessibility features."""

    def test_aria_labels(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "aria-label" in content

    def test_aria_pressed_for_filters(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "aria-pressed" in content

    def test_role_list_for_articles(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert 'role="list"' in content
        assert 'role="listitem"' in content

    def test_role_group_for_filters(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert 'role="group"' in content

    def test_aria_busy_for_loading(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "aria-busy" in content

    def test_touch_targets(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "min-h-[44px]" in content

    def test_search_has_aria_label(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "Buscar articulos educativos" in content

    def test_article_semantic_html(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "<article" in content
        assert "<time" in content


class TestResponsive:
    """Test responsive design."""

    def test_responsive_grid(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "md:grid-cols-2" in content
        assert "lg:grid-cols-3" in content

    def test_responsive_header(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "sm:text-3xl" in content

    def test_featured_responsive(self) -> None:
        content = Path("frontend/src/app/educacion/page.tsx").read_text()
        assert "sm:grid-cols-2" in content
