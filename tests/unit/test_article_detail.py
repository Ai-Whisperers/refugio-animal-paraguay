"""Tests for article detail page with related articles (RAP-627)."""

from __future__ import annotations

from pathlib import Path


class TestPageStructure:
    """Verify article detail page exists."""

    def test_file_exists(self) -> None:
        assert Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").exists()

    def test_is_client_component(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert '"use client"' in content

    def test_exports_default_page(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "export default function ArticleDetailPage" in content

    def test_uses_params(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "useParams" in content
        assert "slug" in content


class TestBreadcrumb:
    """Test breadcrumb navigation."""

    def test_has_breadcrumb(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "Breadcrumb" in content

    def test_links_to_education_hub(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "Centro Educativo" in content
        assert "/educacion" in content

    def test_has_nav_aria_label(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "Ruta de navegacion" in content


class TestArticleHeader:
    """Test article header component."""

    def test_has_article_header(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "ArticleHeader" in content

    def test_shows_category_badge(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "categoryLabels" in content

    def test_shows_read_time(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "min de lectura" in content

    def test_shows_author(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "article.author" in content

    def test_shows_date(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "toLocaleDateString" in content

    def test_shows_tags(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "article.tags" in content


class TestArticleContent:
    """Test article content rendering."""

    def test_has_content_renderer(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "ArticleContent" in content

    def test_renders_headings(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "## " in content
        assert "### " in content

    def test_renders_lists(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "list-disc" in content

    def test_renders_paragraphs(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "leading-relaxed" in content


class TestShareButtons:
    """Test share functionality."""

    def test_has_share_buttons(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "ShareButtons" in content

    def test_has_whatsapp_share(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "wa.me" in content
        assert "WhatsApp" in content

    def test_has_native_share(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "navigator.share" in content

    def test_share_section_label(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "Compartir" in content


class TestRelatedArticles:
    """Test related articles section."""

    def test_has_related_section(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "Articulos relacionados" in content

    def test_has_related_card(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "RelatedArticleCard" in content

    def test_limits_related_count(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "MAX_RELATED_ARTICLES" in content
        assert "3" in content

    def test_related_links_to_articles(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "/educacion/articulos/" in content

    def test_related_shows_category(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "article.category" in content

    def test_has_responsive_grid(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "sm:grid-cols-3" in content


class TestSampleContent:
    """Test sample/fallback content."""

    def test_has_sample_articles(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "SAMPLE_ARTICLES" in content

    def test_has_adoption_article(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "guia-adoptar-perro-paraguay" in content

    def test_has_vaccination_article(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "calendario-vacunacion-mascotas" in content

    def test_sample_related(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "SAMPLE_RELATED" in content


class TestLoadingAndErrorStates:
    """Test loading and error states."""

    def test_has_loading_skeleton(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "LoadingSkeleton" in content
        assert "animate-pulse" in content

    def test_has_not_found_state(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "NotFoundState" in content
        assert "Articulo no encontrado" in content

    def test_not_found_links_back(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "Volver al Centro Educativo" in content


class TestAPIIntegration:
    """Test API integration."""

    def test_fetches_article_by_slug(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "/api/articles/public/" in content

    def test_fetches_related_by_category(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "category=" in content

    def test_falls_back_to_sample(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "SAMPLE_ARTICLES[slug]" in content


class TestAccessibility:
    """Test accessibility features."""

    def test_aria_labels(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "aria-label" in content

    def test_semantic_article_tag(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "<article" in content

    def test_time_element(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "<time" in content
        assert "dateTime" in content

    def test_nav_for_breadcrumb(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "<nav" in content

    def test_role_list_for_related(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert 'role="list"' in content
        assert 'role="listitem"' in content

    def test_role_alert_for_not_found(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert 'role="alert"' in content

    def test_aria_busy_loading(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "aria-busy" in content

    def test_touch_targets(self) -> None:
        content = Path("frontend/src/app/educacion/articulos/[slug]/page.tsx").read_text()
        assert "min-h-[44px]" in content
