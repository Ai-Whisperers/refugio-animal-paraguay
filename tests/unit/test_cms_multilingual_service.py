"""Unit tests for CMS multilingual content service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.cms_service import (
    CMSError,
    ContentNotFoundError,
    InvalidLanguageError,
    TranslationExistsError,
    create_content,
    create_translation,
    get_content_by_slug,
    get_translation_status,
    list_content,
    list_public_content,
    mark_translations_outdated,
    validate_language,
)

# ---------------------------------------------------------------------------
# validate_language
# ---------------------------------------------------------------------------


class TestValidateLanguage:
    """Tests for language code validation."""

    def test_valid_languages(self) -> None:
        for lang in ("es", "en", "de", "nl"):
            validate_language(lang)

    def test_invalid_language_raises(self) -> None:
        with pytest.raises(InvalidLanguageError):
            validate_language("fr")

    def test_empty_language_raises(self) -> None:
        with pytest.raises(InvalidLanguageError):
            validate_language("")


# ---------------------------------------------------------------------------
# create_content with language
# ---------------------------------------------------------------------------


class TestCreateContentWithLanguage:
    """Tests for content creation with language support."""

    @pytest.fixture()
    def mock_db(self) -> AsyncMock:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock
        return db

    @pytest.mark.asyncio()
    async def test_default_language_is_spanish(self, mock_db: AsyncMock) -> None:
        content = await create_content(
            content_type="blog_post",
            title="Test Post",
            body="<p>Hello</p>",
            db=mock_db,
        )
        assert content.language == "es"
        assert content.translation_status == "original"

    @pytest.mark.asyncio()
    async def test_creates_content_in_english(self, mock_db: AsyncMock) -> None:
        content = await create_content(
            content_type="page",
            title="About Us",
            body="<p>About</p>",
            language="en",
            db=mock_db,
        )
        assert content.language == "en"

    @pytest.mark.asyncio()
    async def test_rejects_invalid_language(self, mock_db: AsyncMock) -> None:
        with pytest.raises(InvalidLanguageError):
            await create_content(
                content_type="page",
                title="Test",
                body="body",
                language="fr",
                db=mock_db,
            )


# ---------------------------------------------------------------------------
# get_content_by_slug with language fallback
# ---------------------------------------------------------------------------


class TestGetContentBySlugWithLanguage:
    """Tests for slug lookup with language fallback."""

    @pytest.mark.asyncio()
    async def test_returns_requested_language(self) -> None:
        mock_content = MagicMock()
        mock_content.slug = "about"
        mock_content.language = "en"
        mock_content.status = "published"

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_content
        db.execute.return_value = result

        content, is_fallback = await get_content_by_slug("about", db, language="en")
        assert content.language == "en"
        assert is_fallback is False

    @pytest.mark.asyncio()
    async def test_falls_back_to_spanish(self) -> None:
        mock_es_content = MagicMock()
        mock_es_content.slug = "about"
        mock_es_content.language = "es"
        mock_es_content.status = "published"

        db = AsyncMock()
        # First call (English) returns None, second call (Spanish) returns content
        result_none = MagicMock()
        result_none.scalar_one_or_none.return_value = None
        result_es = MagicMock()
        result_es.scalar_one_or_none.return_value = mock_es_content
        db.execute.side_effect = [result_none, result_es]

        content, is_fallback = await get_content_by_slug("about", db, language="en")
        assert content.language == "es"
        assert is_fallback is True

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_no_language_available(self) -> None:
        db = AsyncMock()
        result_none = MagicMock()
        result_none.scalar_one_or_none.return_value = None
        db.execute.return_value = result_none

        with pytest.raises(ContentNotFoundError):
            await get_content_by_slug("nonexistent", db, language="en")

    @pytest.mark.asyncio()
    async def test_defaults_to_spanish_when_no_lang_param(self) -> None:
        mock_content = MagicMock()
        mock_content.slug = "about"
        mock_content.language = "es"

        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = mock_content
        db.execute.return_value = result

        _content, is_fallback = await get_content_by_slug("about", db)
        assert is_fallback is False

    @pytest.mark.asyncio()
    async def test_no_fallback_when_spanish_requested_and_missing(self) -> None:
        db = AsyncMock()
        result_none = MagicMock()
        result_none.scalar_one_or_none.return_value = None
        db.execute.return_value = result_none

        # Spanish is both requested AND the fallback, so only one query
        with pytest.raises(ContentNotFoundError):
            await get_content_by_slug("missing", db, language="es")

    @pytest.mark.asyncio()
    async def test_rejects_invalid_language_param(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidLanguageError):
            await get_content_by_slug("about", db, language="xx")


# ---------------------------------------------------------------------------
# list_content with language filter
# ---------------------------------------------------------------------------


class TestListContentWithLanguage:
    """Tests for listing content with language filtering."""

    @pytest.mark.asyncio()
    async def test_filters_by_language(self) -> None:
        db = AsyncMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = []
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.side_effect = [items_result, count_result]

        _items, total = await list_content(db, language="en")
        assert total == 0

    @pytest.mark.asyncio()
    async def test_rejects_invalid_language_filter(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidLanguageError):
            await list_content(db, language="xx")


# ---------------------------------------------------------------------------
# list_public_content with language
# ---------------------------------------------------------------------------


class TestListPublicContentWithLanguage:
    """Tests for listing published content with language filter."""

    @pytest.mark.asyncio()
    async def test_defaults_to_spanish(self) -> None:
        db = AsyncMock()
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = []
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute.side_effect = [items_result, count_result]

        _items, total = await list_public_content(db)
        assert total == 0


# ---------------------------------------------------------------------------
# create_translation
# ---------------------------------------------------------------------------


class TestCreateTranslation:
    """Tests for translation creation."""

    def _make_db_with_source(
        self, source_lang: str = "es", existing_translation: bool = False
    ) -> tuple[AsyncMock, MagicMock]:
        source = MagicMock()
        source.id = uuid4()
        source.slug = "about-us"
        source.language = source_lang
        source.content_type = "page"
        source.featured_image_url = "https://example.com/img.jpg"
        source.tags = ["about"]
        source.sort_order = 0

        db = AsyncMock()
        # First call: get_content_by_id
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = source
        # Second call: check existing translation
        check_result = MagicMock()
        check_result.scalar_one_or_none.return_value = uuid4() if existing_translation else None
        db.execute.side_effect = [get_result, check_result]
        return db, source

    @pytest.mark.asyncio()
    async def test_creates_translation(self) -> None:
        db, source = self._make_db_with_source()
        translation = await create_translation(
            source_content_id=source.id,
            language="en",
            title="About Us",
            body="<p>About us in English</p>",
            db=db,
        )
        assert translation.language == "en"
        assert translation.slug == "about-us"
        assert translation.translation_status == "translated"
        assert translation.source_content_id == source.id
        db.add.assert_called_once()

    @pytest.mark.asyncio()
    async def test_rejects_same_language(self) -> None:
        db, source = self._make_db_with_source(source_lang="es")
        with pytest.raises(CMSError, match="Cannot translate to same language"):
            await create_translation(
                source_content_id=source.id,
                language="es",
                title="Title",
                body="Body",
                db=db,
            )

    @pytest.mark.asyncio()
    async def test_rejects_existing_translation(self) -> None:
        db, source = self._make_db_with_source(existing_translation=True)
        with pytest.raises(TranslationExistsError):
            await create_translation(
                source_content_id=source.id,
                language="en",
                title="Title",
                body="Body",
                db=db,
            )

    @pytest.mark.asyncio()
    async def test_rejects_invalid_language(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidLanguageError):
            await create_translation(
                source_content_id=uuid4(),
                language="fr",
                title="Title",
                body="Body",
                db=db,
            )


# ---------------------------------------------------------------------------
# get_translation_status
# ---------------------------------------------------------------------------


class TestGetTranslationStatus:
    """Tests for translation status reporting."""

    @pytest.mark.asyncio()
    async def test_returns_status_for_original(self) -> None:
        content_id = uuid4()
        source = MagicMock()
        source.id = content_id
        source.source_content_id = None
        source.language = "es"
        source.translation_status = "original"
        source.status = "published"
        source.updated_at = "2026-03-28T00:00:00"

        en_translation = MagicMock()
        en_translation.id = uuid4()
        en_translation.source_content_id = content_id
        en_translation.language = "en"
        en_translation.translation_status = "translated"
        en_translation.status = "published"
        en_translation.updated_at = "2026-03-28T01:00:00"

        db = AsyncMock()
        # First call: get_content_by_id
        get_result = MagicMock()
        get_result.scalar_one_or_none.return_value = source
        # Second call: get all translations
        all_result = MagicMock()
        all_result.scalars.return_value.all.return_value = [source, en_translation]
        db.execute.side_effect = [get_result, all_result]

        result = await get_translation_status(content_id, db)
        assert result["source_content_id"] == str(content_id)
        assert "es" in result["languages"]
        assert "en" in result["languages"]
        assert result["completed_translations"] == 2
        assert result["total_supported_languages"] == 4
        assert "2/4" in result["completion_label"]


# ---------------------------------------------------------------------------
# mark_translations_outdated
# ---------------------------------------------------------------------------


class TestMarkTranslationsOutdated:
    """Tests for marking translations as outdated."""

    @pytest.mark.asyncio()
    async def test_marks_translated_as_outdated(self) -> None:
        content_id = uuid4()
        en_translation = MagicMock()
        en_translation.translation_status = "translated"

        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [en_translation]
        db.execute.return_value = result

        count = await mark_translations_outdated(content_id, db)
        assert count == 1
        assert en_translation.translation_status == "outdated"
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_zero_when_no_translations(self) -> None:
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute.return_value = result

        count = await mark_translations_outdated(uuid4(), db)
        assert count == 0
        db.flush.assert_not_awaited()
