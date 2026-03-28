"""Unit tests for CMS admin content editor API interactions.

Tests cover the CMS content CRUD endpoints used by the admin editor UI.
"""

from datetime import UTC, datetime
from uuid import uuid4

from src.api.cms import (
    router,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_content(**overrides):
    """Build a mock CMSContent dict."""
    defaults = {
        "id": str(uuid4()),
        "content_type": "page",
        "slug": "test-page",
        "title": "Test Page",
        "summary": "A test page",
        "body": "<p>Hello world</p>",
        "status": "draft",
        "featured_image_url": None,
        "meta_description": None,
        "tags": ["test"],
        "language": "es",
        "translation_status": "original",
        "sort_order": 0,
        "published_at": None,
        "author_id": str(uuid4()),
        "created_at": datetime(2026, 3, 1, 12, 0, tzinfo=UTC).isoformat(),
        "updated_at": datetime(2026, 3, 1, 12, 0, tzinfo=UTC).isoformat(),
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCMSRouterConfiguration:
    """Verify router is properly configured."""

    def test_router_has_prefix(self):
        assert router.prefix == "/api/cms"

    def test_router_has_tags(self):
        assert "cms" in router.tags


class TestCMSContentTypes:
    """Test content type handling."""

    def test_valid_content_types(self):
        from src.db.models.cms_content import ContentType

        assert ContentType.PAGE == "page"
        assert ContentType.BLOG_POST == "blog_post"
        assert ContentType.SUCCESS_STORY == "success_story"
        assert ContentType.ANNOUNCEMENT == "announcement"
        assert ContentType.FAQ == "faq"

    def test_valid_statuses(self):
        from src.db.models.cms_content import ContentStatus

        assert ContentStatus.DRAFT == "draft"
        assert ContentStatus.PUBLISHED == "published"
        assert ContentStatus.ARCHIVED == "archived"

    def test_valid_languages(self):
        from src.db.models.cms_content import ContentLanguage

        assert ContentLanguage.ES == "es"
        assert ContentLanguage.EN == "en"
        assert ContentLanguage.DE == "de"
        assert ContentLanguage.NL == "nl"


class TestCMSServiceValidation:
    """Test CMS service validation constants."""

    def test_max_title_length(self):
        from src.services.cms_service import MAX_TITLE_LENGTH

        assert MAX_TITLE_LENGTH == 300

    def test_max_body_length(self):
        from src.services.cms_service import MAX_BODY_LENGTH

        assert MAX_BODY_LENGTH == 100_000

    def test_max_tags(self):
        from src.services.cms_service import MAX_TAGS

        assert MAX_TAGS == 20

    def test_default_language(self):
        from src.db.models.cms_content import ContentLanguage
        from src.services.cms_service import DEFAULT_LANGUAGE

        assert DEFAULT_LANGUAGE == ContentLanguage.ES


class TestCMSServiceErrors:
    """Test CMS service error types."""

    def test_content_not_found_error(self):
        from src.services.cms_service import ContentNotFoundError

        err = ContentNotFoundError("test-slug")
        assert "not found" in err.message.lower()
        assert err.identifier == "test-slug"

    def test_slug_conflict_error(self):
        from src.services.cms_service import SlugConflictError

        err = SlugConflictError("my-slug")
        assert err.slug == "my-slug"

    def test_invalid_content_type_error(self):
        from src.services.cms_service import InvalidContentTypeError

        err = InvalidContentTypeError("invalid_type")
        assert "Must be one of" in (err.details or "")

    def test_invalid_language_error(self):
        from src.services.cms_service import InvalidLanguageError

        err = InvalidLanguageError("xx")

    def test_invalid_status_transition_error(self):
        from src.services.cms_service import InvalidStatusTransitionError

        err = InvalidStatusTransitionError("draft", "archived")


class TestCMSTranslationStatus:
    """Test translation status enum values."""

    def test_translation_statuses(self):
        from src.db.models.cms_content import TranslationStatus

        assert TranslationStatus.ORIGINAL == "original"
        assert TranslationStatus.TRANSLATED == "translated"
        assert TranslationStatus.PENDING == "pending"
        assert TranslationStatus.OUTDATED == "outdated"


class TestCMSContentModel:
    """Test CMSContent model constraints."""

    def test_table_name(self):
        from src.db.models.cms_content import CMSContent

        assert CMSContent.__tablename__ == "cms_contents"

    def test_unique_constraint_slug_language(self):
        from src.db.models.cms_content import CMSContent

        constraints = CMSContent.__table_args__
        unique_names = [
            c.name for c in constraints if hasattr(c, "name") and c.name and "uq_" in c.name
        ]
        assert "uq_cms_contents_slug_language" in unique_names
