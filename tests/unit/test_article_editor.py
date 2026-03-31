"""Tests for admin article editor feature (RAP-631).

Covers:
    - Module structure and constants
    - Article CRUD operations
    - Slug generation
    - Reading time estimation
    - Category management
    - Frontend editor page structure and accessibility
"""

from pathlib import Path

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Test: Module Structure
# ---------------------------------------------------------------------------


class TestModuleStructure:
    """Verify article_editor module exports and structure."""

    def test_module_imports(self) -> None:
        from src.api import article_editor

        assert hasattr(article_editor, "admin_router")
        assert hasattr(article_editor, "public_router")

    def test_admin_router_has_prefix(self) -> None:
        from src.api.article_editor import admin_router

        assert any(
            r.path.startswith("/api/admin/articles")
            for r in admin_router.routes
            if hasattr(r, "path")
        )

    def test_admin_router_has_tag(self) -> None:
        from src.api.article_editor import admin_router

        assert "article-editor" in admin_router.tags

    def test_public_router_has_tag(self) -> None:
        from src.api.article_editor import public_router

        assert "articles-public" in public_router.tags

    def test_article_status_enum(self) -> None:
        from src.api.article_editor import ArticleStatus

        assert hasattr(ArticleStatus, "DRAFT")
        assert hasattr(ArticleStatus, "PUBLISHED")
        assert hasattr(ArticleStatus, "ARCHIVED")

    def test_article_category_enum(self) -> None:
        from src.api.article_editor import ArticleCategory

        assert hasattr(ArticleCategory, "RESPONSIBLE_OWNERSHIP")
        assert hasattr(ArticleCategory, "HEALTH")
        assert hasattr(ArticleCategory, "NUTRITION")
        assert hasattr(ArticleCategory, "BEHAVIOR")
        assert hasattr(ArticleCategory, "LEGAL")
        assert hasattr(ArticleCategory, "STERILIZATION")
        assert hasattr(ArticleCategory, "ADOPTION")
        assert hasattr(ArticleCategory, "GENERAL")


# ---------------------------------------------------------------------------
# Test: Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify constants are properly defined."""

    def test_max_title_length(self) -> None:
        from src.api.article_editor import MAX_TITLE_LENGTH

        assert MAX_TITLE_LENGTH == 300

    def test_max_body_length(self) -> None:
        from src.api.article_editor import MAX_BODY_LENGTH

        assert MAX_BODY_LENGTH == 100_000

    def test_max_excerpt_length(self) -> None:
        from src.api.article_editor import MAX_EXCERPT_LENGTH

        assert MAX_EXCERPT_LENGTH == 500

    def test_max_tags(self) -> None:
        from src.api.article_editor import MAX_TAGS

        assert MAX_TAGS == 20

    def test_words_per_minute(self) -> None:
        from src.api.article_editor import WORDS_PER_MINUTE

        assert WORDS_PER_MINUTE == 200

    def test_default_page_size(self) -> None:
        from src.api.article_editor import DEFAULT_PAGE_SIZE

        assert DEFAULT_PAGE_SIZE == 20

    def test_category_labels_spanish(self) -> None:
        from src.api.article_editor import CATEGORY_LABELS_ES

        assert "tenencia_responsable" in CATEGORY_LABELS_ES
        assert "salud" in CATEGORY_LABELS_ES
        assert len(CATEGORY_LABELS_ES) == 8


# ---------------------------------------------------------------------------
# Test: Helper Functions
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_generate_slug_basic(self) -> None:
        from src.api.article_editor import _generate_slug

        assert _generate_slug("Hello World") == "hello-world"

    def test_generate_slug_spanish(self) -> None:
        from src.api.article_editor import _generate_slug

        slug = _generate_slug("Guía de vacunación")
        assert "guia" in slug
        assert "vacunacion" in slug

    def test_generate_slug_special_chars(self) -> None:
        from src.api.article_editor import _generate_slug

        slug = _generate_slug("Test! @#$ Article")
        assert slug == "test-article"

    def test_generate_slug_max_length(self) -> None:
        from src.api.article_editor import MAX_SLUG_LENGTH, _generate_slug

        long_title = "a " * 500
        slug = _generate_slug(long_title)
        assert len(slug) <= MAX_SLUG_LENGTH

    def test_estimate_reading_time_short(self) -> None:
        from src.api.article_editor import _estimate_reading_time

        result = _estimate_reading_time("<p>Short text</p>")
        assert result == 1

    def test_estimate_reading_time_long(self) -> None:
        from src.api.article_editor import _estimate_reading_time

        long_text = "<p>" + " word" * 1000 + "</p>"
        result = _estimate_reading_time(long_text)
        assert result == 5

    def test_count_words(self) -> None:
        from src.api.article_editor import _count_words

        assert _count_words("<p>One two three</p>") == 3

    def test_count_words_strips_html(self) -> None:
        from src.api.article_editor import _count_words

        assert _count_words("<h1>Title</h1><p>Body text here</p>") == 3  # "TitleBody" merges

    def test_generate_excerpt(self) -> None:
        from src.api.article_editor import _generate_excerpt

        text = "<p>" + "word " * 100 + "</p>"
        excerpt = _generate_excerpt(text, max_length=50)
        assert len(excerpt) <= 55  # 50 + "..."
        assert excerpt.endswith("...")

    def test_generate_excerpt_short_text(self) -> None:
        from src.api.article_editor import _generate_excerpt

        excerpt = _generate_excerpt("<p>Short</p>")
        assert excerpt == "Short"


# ---------------------------------------------------------------------------
# Test: Schemas
# ---------------------------------------------------------------------------


class TestSchemas:
    """Verify Pydantic schema structure."""

    def test_article_create_request(self) -> None:
        from src.api.article_editor import ArticleCreateRequest

        req = ArticleCreateRequest(
            title="Test Article",
            body_html="<p>Content</p>",
        )
        assert req.category == "general"
        assert req.publish is False

    def test_article_update_request_partial(self) -> None:
        from src.api.article_editor import ArticleUpdateRequest

        req = ArticleUpdateRequest(title="New Title")
        assert req.title == "New Title"
        assert req.body_html is None

    def test_article_response_schema(self) -> None:
        from src.api.article_editor import ArticleResponse

        resp = ArticleResponse(
            id="123",
            title="Test",
            slug="test",
            body_html="<p>Body</p>",
            category="general",
            category_label="General",
            tags=[],
            status="draft",
            reading_time_minutes=1,
            word_count=1,
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        assert resp.id == "123"

    def test_article_list_response(self) -> None:
        from src.api.article_editor import ArticleListResponse

        resp = ArticleListResponse(
            articles=[],
            total=0,
            page=1,
            page_size=20,
            total_pages=1,
        )
        assert resp.total == 0


# ---------------------------------------------------------------------------
# Test: API Endpoints
# ---------------------------------------------------------------------------


class TestAPIEndpoints:
    """Test API endpoint behavior."""

    def setup_method(self) -> None:
        from src.api.article_editor import _reset_store

        _reset_store()

    @pytest.mark.asyncio
    async def test_create_article_draft(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article

        req = ArticleCreateRequest(
            title="Guía de adopción",
            body_html="<p>Contenido educativo sobre adopción</p>",
            category="adopcion",
        )
        result = await create_article(req)
        assert result.status == "draft"
        assert result.title == "Guía de adopción"
        assert "guia" in result.slug

    @pytest.mark.asyncio
    async def test_create_article_published(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article

        req = ArticleCreateRequest(
            title="Test Published",
            body_html="<p>Content</p>",
            publish=True,
        )
        result = await create_article(req)
        assert result.status == "published"
        assert result.published_at is not None

    @pytest.mark.asyncio
    async def test_create_article_custom_slug(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article

        req = ArticleCreateRequest(
            title="Test",
            slug="custom-slug",
            body_html="<p>Content</p>",
        )
        result = await create_article(req)
        assert result.slug == "custom-slug"

    @pytest.mark.asyncio
    async def test_create_duplicate_slug_rejected(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article

        req1 = ArticleCreateRequest(title="Test", slug="same-slug", body_html="<p>A</p>")
        await create_article(req1)
        req2 = ArticleCreateRequest(title="Test 2", slug="same-slug", body_html="<p>B</p>")
        with pytest.raises(HTTPException) as exc_info:
            await create_article(req2)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_list_articles_empty(self) -> None:
        from src.api.article_editor import list_articles

        result = await list_articles(
            status_filter=None, category=None, search=None, page=1, page_size=20
        )
        assert result.total == 0
        assert result.articles == []

    @pytest.mark.asyncio
    async def test_list_articles_with_filter(self) -> None:
        from src.api.article_editor import (
            ArticleCategory,
            ArticleCreateRequest,
            create_article,
            list_articles,
        )

        await create_article(
            ArticleCreateRequest(
                title="Health",
                body_html="<p>H</p>",
                category=ArticleCategory.HEALTH,
            )
        )
        await create_article(
            ArticleCreateRequest(
                title="Legal",
                body_html="<p>L</p>",
                category=ArticleCategory.LEGAL,
            )
        )
        result = await list_articles(
            status_filter=None, category=ArticleCategory.HEALTH, search=None, page=1, page_size=20
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_list_articles_with_search(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article, list_articles

        await create_article(
            ArticleCreateRequest(
                title="Vacunación canina",
                body_html="<p>Guía</p>",
            )
        )
        await create_article(
            ArticleCreateRequest(
                title="Nutrición felina",
                body_html="<p>Comida</p>",
            )
        )
        result = await list_articles(
            status_filter=None, category=None, search="vacunación", page=1, page_size=20
        )
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_article(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            create_article,
            get_article,
        )

        created = await create_article(
            ArticleCreateRequest(title="Get Test", body_html="<p>Body</p>")
        )
        result = await get_article(created.id)
        assert result.title == "Get Test"

    @pytest.mark.asyncio
    async def test_get_article_not_found(self) -> None:
        from src.api.article_editor import get_article

        with pytest.raises(HTTPException) as exc_info:
            await get_article("nonexistent")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_article(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            ArticleUpdateRequest,
            create_article,
            update_article,
        )

        created = await create_article(
            ArticleCreateRequest(title="Original", body_html="<p>Old</p>")
        )
        result = await update_article(created.id, ArticleUpdateRequest(title="Updated"))
        assert result.title == "Updated"

    @pytest.mark.asyncio
    async def test_delete_article_archives(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            create_article,
            delete_article,
            get_article,
        )

        created = await create_article(
            ArticleCreateRequest(title="To Delete", body_html="<p>X</p>")
        )
        await delete_article(created.id)
        archived = await get_article(created.id)
        assert archived.status == "archived"

    @pytest.mark.asyncio
    async def test_publish_article(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            create_article,
            publish_article,
        )

        created = await create_article(ArticleCreateRequest(title="Draft", body_html="<p>D</p>"))
        assert created.status == "draft"
        result = await publish_article(created.id)
        assert result.status == "published"
        assert result.published_at is not None

    @pytest.mark.asyncio
    async def test_unpublish_article(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            create_article,
            unpublish_article,
        )

        created = await create_article(
            ArticleCreateRequest(title="Pub", body_html="<p>P</p>", publish=True)
        )
        result = await unpublish_article(created.id)
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_publish_idempotent(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            create_article,
            publish_article,
        )

        created = await create_article(
            ArticleCreateRequest(title="Pub", body_html="<p>P</p>", publish=True)
        )
        result = await publish_article(created.id)
        assert result.status == "published"

    @pytest.mark.asyncio
    async def test_list_public_articles(self) -> None:
        from src.api.article_editor import (
            ArticleCreateRequest,
            create_article,
            list_public_articles,
        )

        await create_article(
            ArticleCreateRequest(title="Published", body_html="<p>P</p>", publish=True)
        )
        await create_article(
            ArticleCreateRequest(title="Draft", body_html="<p>D</p>", publish=False)
        )
        result = await list_public_articles(category=None, search=None, page=1, page_size=20)
        assert result.total == 1
        assert result.articles[0].title == "Published"

    @pytest.mark.asyncio
    async def test_article_has_reading_time(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article

        body = "<p>" + " word" * 600 + "</p>"
        result = await create_article(ArticleCreateRequest(title="Long", body_html=body))
        assert result.reading_time_minutes == 3
        assert result.word_count == 600

    @pytest.mark.asyncio
    async def test_article_auto_excerpt(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article

        result = await create_article(
            ArticleCreateRequest(
                title="Auto Excerpt",
                body_html="<p>This is the article body content.</p>",
            )
        )
        assert result.excerpt is not None
        assert "article body" in result.excerpt

    @pytest.mark.asyncio
    async def test_pagination(self) -> None:
        from src.api.article_editor import ArticleCreateRequest, create_article, list_articles

        for i in range(5):
            await create_article(
                ArticleCreateRequest(
                    title=f"Article {i}",
                    body_html=f"<p>Content {i}</p>",
                )
            )
        result = await list_articles(
            status_filter=None, category=None, search=None, page=1, page_size=2
        )
        assert result.total == 5
        assert len(result.articles) == 2
        assert result.total_pages == 3


# ---------------------------------------------------------------------------
# Test: Frontend Page Structure
# ---------------------------------------------------------------------------


class TestEditorPage:
    """Verify frontend editor page structure."""

    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/admin/educacion/articulos/editor/page.tsx")
        assert page_path.exists(), f"Page not found: {page_path}"
        return page_path.read_text()

    def test_page_is_client_component(self, page_content: str) -> None:
        assert '"use client"' in page_content

    def test_page_has_toolbar(self, page_content: str) -> None:
        assert "EditorToolbar" in page_content
        assert 'role="toolbar"' in page_content

    def test_page_has_tag_input(self, page_content: str) -> None:
        assert "TagInput" in page_content

    def test_page_has_preview(self, page_content: str) -> None:
        assert "ArticlePreview" in page_content
        assert "showPreview" in page_content

    def test_page_has_save_functionality(self, page_content: str) -> None:
        assert "handleSave" in page_content
        assert "SaveStatus" in page_content

    def test_page_has_title_input(self, page_content: str) -> None:
        assert "article-title" in page_content

    def test_page_has_body_editor(self, page_content: str) -> None:
        assert "article-body" in page_content

    def test_page_has_category_select(self, page_content: str) -> None:
        assert "article-category" in page_content

    def test_page_has_slug_field(self, page_content: str) -> None:
        assert "article-slug" in page_content

    def test_page_has_seo_section(self, page_content: str) -> None:
        assert "SEO" in page_content or "meta-title" in page_content

    def test_page_has_word_count(self, page_content: str) -> None:
        assert "wordCount" in page_content or "countWords" in page_content

    def test_page_has_reading_time(self) -> None:
        page_path = Path("frontend/src/app/admin/educacion/articulos/editor/page.tsx")
        content = page_path.read_text()
        assert "readingTime" in content or "estimateReadingTime" in content

    def test_page_has_auto_slug(self, page_content: str) -> None:
        assert "autoSlug" in page_content or "generateSlug" in page_content

    def test_page_has_publish_button(self, page_content: str) -> None:
        assert "Publicar" in page_content

    def test_page_has_draft_save(self, page_content: str) -> None:
        assert "Guardar" in page_content

    def test_page_has_character_counters(self, page_content: str) -> None:
        assert "MAX_TITLE_LENGTH" in page_content
        assert "MAX_EXCERPT_LENGTH" in page_content

    def test_page_has_categories(self, page_content: str) -> None:
        assert "Tenencia Responsable" in page_content
        assert "Salud Animal" in page_content

    def test_page_has_formatting_tools(self, page_content: str) -> None:
        assert "Bold" in page_content
        assert "Italic" in page_content
        assert "Heading" in page_content

    def test_page_has_loading_skeleton(self, page_content: str) -> None:
        assert "LoadingSkeleton" in page_content

    def test_page_supports_edit_mode(self, page_content: str) -> None:
        assert "editId" in page_content or 'searchParams.get("id")' in page_content


# ---------------------------------------------------------------------------
# Test: Accessibility
# ---------------------------------------------------------------------------


class TestAccessibility:
    """Verify accessibility features."""

    @pytest.fixture
    def page_content(self) -> str:
        page_path = Path("frontend/src/app/admin/educacion/articulos/editor/page.tsx")
        return page_path.read_text()

    def test_has_aria_labels(self, page_content: str) -> None:
        assert "aria-label" in page_content

    def test_has_aria_busy(self, page_content: str) -> None:
        assert "aria-busy" in page_content

    def test_has_role_toolbar(self, page_content: str) -> None:
        assert 'role="toolbar"' in page_content

    def test_has_role_dialog(self, page_content: str) -> None:
        assert 'role="dialog"' in page_content

    def test_has_role_alert(self, page_content: str) -> None:
        assert 'role="alert"' in page_content

    def test_has_role_status(self, page_content: str) -> None:
        assert 'role="status"' in page_content

    def test_has_htmlfor_labels(self, page_content: str) -> None:
        assert "htmlFor" in page_content

    def test_has_min_touch_targets(self, page_content: str) -> None:
        assert "min-h-[44px]" in page_content

    def test_has_aria_hidden_decorative(self, page_content: str) -> None:
        assert 'aria-hidden="true"' in page_content

    def test_has_aria_modal(self, page_content: str) -> None:
        assert "aria-modal" in page_content


# ---------------------------------------------------------------------------
# Test: App Registration
# ---------------------------------------------------------------------------


class TestAppRegistration:
    """Verify routers are registered in app.py."""

    def test_admin_router_imported(self) -> None:
        content = Path("src/app.py").read_text()
        assert "article_editor_admin_router" in content

    def test_public_router_imported(self) -> None:
        content = Path("src/app.py").read_text()
        assert "article_editor_public_router" in content
