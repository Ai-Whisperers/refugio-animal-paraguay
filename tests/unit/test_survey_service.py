"""Unit tests for survey service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.survey_service import (
    DEFAULT_PAGE_SIZE,
    DuplicateResponseError,
    InvalidQuestionsError,
    SurveyError,
    SurveyNotActiveError,
    SurveyNotFoundError,
    create_survey,
    delete_survey,
    get_survey,
    list_surveys,
    submit_response,
    update_survey,
    validate_questions,
)

# --- Test Error Classes ---


class TestErrorClasses:
    """Tests for error hierarchy."""

    def test_survey_error_is_exception(self) -> None:
        assert isinstance(SurveyError("test"), Exception)

    def test_not_found_is_survey_error(self) -> None:
        assert isinstance(SurveyNotFoundError("x"), SurveyError)

    def test_not_active_is_survey_error(self) -> None:
        assert isinstance(SurveyNotActiveError("x"), SurveyError)

    def test_duplicate_response_is_survey_error(self) -> None:
        assert isinstance(DuplicateResponseError("x"), SurveyError)

    def test_invalid_questions_is_survey_error(self) -> None:
        assert isinstance(InvalidQuestionsError("x"), SurveyError)


# --- Test validate_questions ---


class TestValidateQuestions:
    """Tests for question schema validation."""

    def test_empty_questions_raises(self) -> None:
        with pytest.raises(InvalidQuestionsError, match="at least one question"):
            validate_questions([])

    def test_non_dict_question_raises(self) -> None:
        with pytest.raises(InvalidQuestionsError, match="must be an object"):
            validate_questions(["not a dict"])

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(InvalidQuestionsError, match="invalid type"):
            validate_questions([{"type": "dropdown", "question": "Pick one"}])

    def test_missing_question_text_raises(self) -> None:
        with pytest.raises(InvalidQuestionsError, match="'question' field is required"):
            validate_questions([{"type": "text"}])

    def test_radio_without_options_raises(self) -> None:
        with pytest.raises(InvalidQuestionsError, match="requires a non-empty 'options'"):
            validate_questions([{"type": "radio", "question": "Pick one"}])

    def test_checkbox_with_empty_options_raises(self) -> None:
        with pytest.raises(InvalidQuestionsError, match="requires a non-empty 'options'"):
            validate_questions([{"type": "checkbox", "question": "Select all", "options": []}])

    def test_valid_text_question(self) -> None:
        validate_questions([{"type": "text", "question": "Your name?"}])

    def test_valid_rating_question(self) -> None:
        validate_questions([{"type": "rating", "question": "Rate us"}])

    def test_valid_radio_question(self) -> None:
        validate_questions([{"type": "radio", "question": "Favorite?", "options": ["A", "B"]}])

    def test_valid_checkbox_question(self) -> None:
        validate_questions([{"type": "checkbox", "question": "Select", "options": ["X", "Y"]}])

    def test_multiple_valid_questions(self) -> None:
        validate_questions(
            [
                {"type": "text", "question": "Name?"},
                {"type": "radio", "question": "Color?", "options": ["Red", "Blue"]},
                {"type": "rating", "question": "Score?"},
            ]
        )


# --- Test create_survey ---


class TestCreateSurvey:
    """Tests for survey creation."""

    @pytest.mark.asyncio
    async def test_creates_survey_successfully(self) -> None:
        db = AsyncMock()
        survey_id = uuid4()
        user_id = uuid4()
        now = datetime.now(UTC)

        mock_survey = MagicMock()
        mock_survey.id = survey_id
        mock_survey.title = "Test Survey"
        mock_survey.description = None
        mock_survey.questions = [{"type": "text", "question": "Name?"}]
        mock_survey.is_active = False
        mock_survey.start_date = None
        mock_survey.end_date = None
        mock_survey.created_by = user_id
        mock_survey.created_at = now
        mock_survey.updated_at = now

        async def fake_refresh(obj):
            for attr in (
                "id",
                "title",
                "description",
                "questions",
                "is_active",
                "start_date",
                "end_date",
                "created_by",
                "created_at",
                "updated_at",
            ):
                setattr(obj, attr, getattr(mock_survey, attr))

        db.refresh = fake_refresh

        result = await create_survey(
            db=db,
            title="Test Survey",
            questions=[{"type": "text", "question": "Name?"}],
            created_by=user_id,
        )

        assert result["title"] == "Test Survey"
        assert db.add.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_invalid_questions_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(InvalidQuestionsError):
            await create_survey(
                db=db,
                title="Bad",
                questions=[],
                created_by=uuid4(),
            )


# --- Test get_survey ---


class TestGetSurvey:
    """Tests for fetching a single survey."""

    @pytest.mark.asyncio
    async def test_returns_survey(self) -> None:
        db = AsyncMock()
        survey_id = uuid4()
        now = datetime.now(UTC)

        mock_survey = MagicMock()
        mock_survey.id = survey_id
        mock_survey.title = "Found"
        mock_survey.description = None
        mock_survey.questions = []
        mock_survey.is_active = True
        mock_survey.start_date = None
        mock_survey.end_date = None
        mock_survey.created_by = uuid4()
        mock_survey.created_at = now
        mock_survey.updated_at = now

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = result_mock

        result = await get_survey(db, survey_id)
        assert result["id"] == survey_id
        assert result["title"] == "Found"

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotFoundError):
            await get_survey(db, uuid4())


# --- Test list_surveys ---


class TestListSurveys:
    """Tests for listing surveys."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self) -> None:
        db = AsyncMock()

        # First call: count
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        # Second call: surveys
        now = datetime.now(UTC)
        s1 = MagicMock()
        s1.id = uuid4()
        s1.title = "S1"
        s1.description = None
        s1.questions = []
        s1.is_active = True
        s1.start_date = None
        s1.end_date = None
        s1.created_by = uuid4()
        s1.created_at = now
        s1.updated_at = now

        surveys_result = MagicMock()
        surveys_scalars = MagicMock()
        surveys_scalars.all.return_value = [s1]
        surveys_result.scalars.return_value = surveys_scalars

        db.execute.side_effect = [count_result, surveys_result]

        result = await list_surveys(db, limit=10, offset=0)
        assert result["total"] == 2
        assert len(result["surveys"]) == 1
        assert result["limit"] == 10

    @pytest.mark.asyncio
    async def test_empty_list(self) -> None:
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0

        surveys_result = MagicMock()
        surveys_scalars = MagicMock()
        surveys_scalars.all.return_value = []
        surveys_result.scalars.return_value = surveys_scalars

        db.execute.side_effect = [count_result, surveys_result]

        result = await list_surveys(db)
        assert result["total"] == 0
        assert result["surveys"] == []
        assert result["limit"] == DEFAULT_PAGE_SIZE


# --- Test update_survey ---


class TestUpdateSurvey:
    """Tests for survey updates."""

    @pytest.mark.asyncio
    async def test_updates_title(self) -> None:
        db = AsyncMock()
        now = datetime.now(UTC)

        mock_survey = MagicMock()
        mock_survey.id = uuid4()
        mock_survey.title = "Old Title"
        mock_survey.description = None
        mock_survey.questions = [{"type": "text", "question": "Q?"}]
        mock_survey.is_active = False
        mock_survey.start_date = None
        mock_survey.end_date = None
        mock_survey.created_by = uuid4()
        mock_survey.created_at = now
        mock_survey.updated_at = now

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = result_mock

        async def fake_refresh(obj):
            obj.title = "New Title"

        db.refresh = fake_refresh

        await update_survey(db, mock_survey.id, title="New Title")
        assert mock_survey.title == "New Title"

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotFoundError):
            await update_survey(db, uuid4(), title="X")


# --- Test delete_survey ---


class TestDeleteSurvey:
    """Tests for survey deletion."""

    @pytest.mark.asyncio
    async def test_deletes_survey(self) -> None:
        db = AsyncMock()
        mock_survey = MagicMock()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = result_mock

        await delete_survey(db, uuid4())
        assert db.delete.called
        assert db.flush.called

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotFoundError):
            await delete_survey(db, uuid4())


# --- Test submit_response ---


class TestSubmitResponse:
    """Tests for survey response submission."""

    @pytest.mark.asyncio
    async def test_submits_response_successfully(self) -> None:
        db = AsyncMock()
        survey_id = uuid4()
        now = datetime.now(UTC)

        mock_survey = MagicMock()
        mock_survey.id = survey_id
        mock_survey.is_active = True
        mock_survey.start_date = None
        mock_survey.end_date = None

        # First call: fetch survey
        survey_result = MagicMock()
        survey_result.scalar_one_or_none.return_value = mock_survey

        # Second call: duplicate check (email provided)
        dup_result = MagicMock()
        dup_result.scalar_one.return_value = 0

        db.execute.side_effect = [survey_result, dup_result]

        mock_response = MagicMock()
        mock_response.id = uuid4()
        mock_response.survey_id = survey_id
        mock_response.respondent_email = "test@example.com"
        mock_response.respondent_user_id = None
        mock_response.answers = {"q1": "yes"}
        mock_response.created_at = now

        async def fake_refresh(obj):
            for attr in (
                "id",
                "survey_id",
                "respondent_email",
                "respondent_user_id",
                "answers",
                "created_at",
            ):
                setattr(obj, attr, getattr(mock_response, attr))

        db.refresh = fake_refresh

        result = await submit_response(
            db=db,
            survey_id=survey_id,
            answers={"q1": "yes"},
            respondent_email="test@example.com",
        )

        assert result["survey_id"] == survey_id
        assert db.add.called

    @pytest.mark.asyncio
    async def test_not_found_raises(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotFoundError):
            await submit_response(db, uuid4(), {"q1": "a"})

    @pytest.mark.asyncio
    async def test_inactive_survey_raises(self) -> None:
        db = AsyncMock()
        mock_survey = MagicMock()
        mock_survey.is_active = False

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotActiveError, match="not active"):
            await submit_response(db, uuid4(), {"q1": "a"})

    @pytest.mark.asyncio
    async def test_survey_not_started_raises(self) -> None:
        db = AsyncMock()
        mock_survey = MagicMock()
        mock_survey.is_active = True
        mock_survey.start_date = datetime.now(UTC) + timedelta(days=1)
        mock_survey.end_date = None

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotActiveError, match="not started"):
            await submit_response(db, uuid4(), {"q1": "a"})

    @pytest.mark.asyncio
    async def test_survey_ended_raises(self) -> None:
        db = AsyncMock()
        mock_survey = MagicMock()
        mock_survey.is_active = True
        mock_survey.start_date = None
        mock_survey.end_date = datetime.now(UTC) - timedelta(days=1)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = result_mock

        with pytest.raises(SurveyNotActiveError, match="ended"):
            await submit_response(db, uuid4(), {"q1": "a"})

    @pytest.mark.asyncio
    async def test_duplicate_email_raises(self) -> None:
        db = AsyncMock()
        mock_survey = MagicMock()
        mock_survey.is_active = True
        mock_survey.start_date = None
        mock_survey.end_date = None

        survey_result = MagicMock()
        survey_result.scalar_one_or_none.return_value = mock_survey

        dup_result = MagicMock()
        dup_result.scalar_one.return_value = 1  # duplicate exists

        db.execute.side_effect = [survey_result, dup_result]

        with pytest.raises(DuplicateResponseError):
            await submit_response(db, uuid4(), {"q1": "a"}, respondent_email="dup@example.com")

    @pytest.mark.asyncio
    async def test_no_email_skips_duplicate_check(self) -> None:
        db = AsyncMock()
        survey_id = uuid4()
        now = datetime.now(UTC)

        mock_survey = MagicMock()
        mock_survey.id = survey_id
        mock_survey.is_active = True
        mock_survey.start_date = None
        mock_survey.end_date = None

        survey_result = MagicMock()
        survey_result.scalar_one_or_none.return_value = mock_survey
        db.execute.return_value = survey_result

        mock_response = MagicMock()
        mock_response.id = uuid4()
        mock_response.survey_id = survey_id
        mock_response.respondent_email = None
        mock_response.respondent_user_id = None
        mock_response.answers = {"q1": "a"}
        mock_response.created_at = now

        async def fake_refresh(obj):
            for attr in (
                "id",
                "survey_id",
                "respondent_email",
                "respondent_user_id",
                "answers",
                "created_at",
            ):
                setattr(obj, attr, getattr(mock_response, attr))

        db.refresh = fake_refresh

        result = await submit_response(db, survey_id, {"q1": "a"})
        assert result["respondent_email"] is None
        # Only one execute call (fetch survey), no duplicate check
        assert db.execute.call_count == 1
