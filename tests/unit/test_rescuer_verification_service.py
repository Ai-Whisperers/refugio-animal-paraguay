"""Unit tests for rescuer verification service."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.services.rescuer_verification_service import (
    MAX_EVIDENCE_NOTES_LENGTH,
    MAX_EVIDENCE_URL_LENGTH,
    MAX_PENDING_REQUESTS_PER_RESCUER,
    MAX_REVIEWER_NOTES_LENGTH,
    VALID_METHODS,
    AlreadyVerifiedError,
    InvalidReviewTransitionError,
    RescuerNotFoundError,
    TooManyPendingRequestsError,
    VerificationError,
    VerificationNotFoundError,
    get_my_verification_requests,
    get_verification_request,
    list_pending_requests,
    review_verification_request,
    submit_verification_request,
    validate_evidence_notes,
    validate_evidence_url,
    validate_method,
    validate_reviewer_notes,
)

# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidateMethod:
    """Tests for verification method validation."""

    def test_accepts_whatsapp(self) -> None:
        validate_method("whatsapp")

    def test_accepts_social(self) -> None:
        validate_method("social")

    def test_accepts_manual(self) -> None:
        validate_method("manual")

    def test_rejects_invalid(self) -> None:
        with pytest.raises(VerificationError, match="Invalid verification method"):
            validate_method("email")

    def test_rejects_empty(self) -> None:
        with pytest.raises(VerificationError, match="Invalid verification method"):
            validate_method("")


class TestValidateEvidenceNotes:
    """Tests for evidence notes validation."""

    def test_accepts_none(self) -> None:
        validate_evidence_notes(None)

    def test_accepts_valid(self) -> None:
        validate_evidence_notes("Here is my evidence.")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(VerificationError, match="Evidence notes too long"):
            validate_evidence_notes("A" * (MAX_EVIDENCE_NOTES_LENGTH + 1))

    def test_accepts_max_length(self) -> None:
        validate_evidence_notes("A" * MAX_EVIDENCE_NOTES_LENGTH)


class TestValidateEvidenceUrl:
    """Tests for evidence URL validation."""

    def test_accepts_none(self) -> None:
        validate_evidence_url(None)

    def test_accepts_valid(self) -> None:
        validate_evidence_url("https://example.com/proof.jpg")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(VerificationError, match="Evidence URL too long"):
            validate_evidence_url("https://x.com/" + "a" * MAX_EVIDENCE_URL_LENGTH)

    def test_accepts_max_length(self) -> None:
        validate_evidence_url("A" * MAX_EVIDENCE_URL_LENGTH)


class TestValidateReviewerNotes:
    """Tests for reviewer notes validation."""

    def test_accepts_none(self) -> None:
        validate_reviewer_notes(None)

    def test_accepts_valid(self) -> None:
        validate_reviewer_notes("Looks good, approved.")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(VerificationError, match="Reviewer notes too long"):
            validate_reviewer_notes("A" * (MAX_REVIEWER_NOTES_LENGTH + 1))


# ---------------------------------------------------------------------------
# submit_verification_request tests
# ---------------------------------------------------------------------------


def _mock_profile(is_verified: bool = False) -> MagicMock:
    """Create a mock rescuer profile."""
    profile = MagicMock()
    profile.id = uuid4()
    profile.user_id = uuid4()
    profile.is_verified = is_verified
    return profile


def _mock_db_with_profile(profile: MagicMock, pending_count: int = 0) -> AsyncMock:
    """Mock DB that returns a profile on first query and pending count on second."""
    db = AsyncMock()
    call_count = 0

    def mock_execute(query):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            # First call: _get_rescuer_profile
            result.scalar_one_or_none.return_value = profile
        else:
            # Second call: _count_pending_requests
            result.all.return_value = [MagicMock() for _ in range(pending_count)]
        call_count += 1
        return result

    db.execute = AsyncMock(side_effect=mock_execute)
    return db


def _mock_db_no_profile() -> AsyncMock:
    """Mock DB that returns no profile."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    return db


class TestSubmitVerificationRequest:
    """Tests for submitting verification requests."""

    @pytest.mark.asyncio
    async def test_successful_submission(self) -> None:
        profile = _mock_profile()
        db = _mock_db_with_profile(profile, pending_count=0)

        request = await submit_verification_request(
            user_id=profile.user_id,
            method="whatsapp",
            evidence_notes="My WhatsApp is verified",
            db=db,
        )
        assert request.method == "whatsapp"
        assert request.rescuer_profile_id == profile.id
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_no_profile(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerNotFoundError):
            await submit_verification_request(
                user_id=uuid4(),
                method="whatsapp",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_already_verified(self) -> None:
        profile = _mock_profile(is_verified=True)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = profile
        db.execute.return_value = mock_result

        with pytest.raises(AlreadyVerifiedError):
            await submit_verification_request(
                user_id=profile.user_id,
                method="social",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_invalid_method(self) -> None:
        profile = _mock_profile()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = profile
        db.execute.return_value = mock_result

        with pytest.raises(VerificationError, match="Invalid verification method"):
            await submit_verification_request(
                user_id=profile.user_id,
                method="invalid",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_too_many_pending(self) -> None:
        profile = _mock_profile()
        db = _mock_db_with_profile(profile, pending_count=MAX_PENDING_REQUESTS_PER_RESCUER)

        with pytest.raises(TooManyPendingRequestsError):
            await submit_verification_request(
                user_id=profile.user_id,
                method="social",
                db=db,
            )

    @pytest.mark.asyncio
    async def test_sets_optional_fields(self) -> None:
        profile = _mock_profile()
        db = _mock_db_with_profile(profile, pending_count=0)

        request = await submit_verification_request(
            user_id=profile.user_id,
            method="social",
            evidence_url="https://instagram.com/rescuer",
            evidence_notes="My Instagram profile",
            db=db,
        )
        assert request.evidence_url == "https://instagram.com/rescuer"
        assert request.evidence_notes == "My Instagram profile"


# ---------------------------------------------------------------------------
# review_verification_request tests
# ---------------------------------------------------------------------------


def _mock_pending_request() -> MagicMock:
    """Create a mock pending verification request."""
    req = MagicMock()
    req.id = uuid4()
    req.rescuer_profile_id = uuid4()
    req.status = "pending"
    req.method = "whatsapp"
    return req


def _mock_db_for_review(request: MagicMock | None, profile: MagicMock | None = None) -> AsyncMock:
    """Mock DB for review operations."""
    db = AsyncMock()
    call_count = 0

    def mock_execute(query):
        nonlocal call_count
        result = MagicMock()
        if call_count == 0:
            # First call: get verification request
            result.scalar_one_or_none.return_value = request
        else:
            # Second call: get rescuer profile (for approval)
            result.scalar_one_or_none.return_value = profile
        call_count += 1
        return result

    db.execute = AsyncMock(side_effect=mock_execute)
    return db


class TestReviewVerificationRequest:
    """Tests for reviewing verification requests."""

    @pytest.mark.asyncio
    async def test_approve_marks_profile_verified(self) -> None:
        req = _mock_pending_request()
        profile = _mock_profile()
        db = _mock_db_for_review(req, profile)
        reviewer_id = uuid4()

        result = await review_verification_request(
            request_id=req.id,
            reviewer_user_id=reviewer_id,
            approved=True,
            reviewer_notes="Verified via WhatsApp",
            db=db,
        )
        assert result.status == "approved"
        assert result.reviewer_user_id == reviewer_id
        assert result.reviewer_notes == "Verified via WhatsApp"
        assert result.reviewed_at is not None
        # Profile should be marked as verified
        assert profile.is_verified is True
        assert profile.verification_method == req.method

    @pytest.mark.asyncio
    async def test_reject_does_not_verify_profile(self) -> None:
        req = _mock_pending_request()
        db = _mock_db_for_review(req)
        reviewer_id = uuid4()

        result = await review_verification_request(
            request_id=req.id,
            reviewer_user_id=reviewer_id,
            approved=False,
            reviewer_notes="Insufficient evidence",
            db=db,
        )
        assert result.status == "rejected"
        assert result.reviewer_notes == "Insufficient evidence"

    @pytest.mark.asyncio
    async def test_rejects_not_found(self) -> None:
        db = _mock_db_for_review(None)
        with pytest.raises(VerificationNotFoundError):
            await review_verification_request(
                request_id=uuid4(),
                reviewer_user_id=uuid4(),
                approved=True,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_already_reviewed(self) -> None:
        req = _mock_pending_request()
        req.status = "approved"
        db = _mock_db_for_review(req)

        with pytest.raises(InvalidReviewTransitionError):
            await review_verification_request(
                request_id=req.id,
                reviewer_user_id=uuid4(),
                approved=True,
                db=db,
            )

    @pytest.mark.asyncio
    async def test_rejects_long_reviewer_notes(self) -> None:
        with pytest.raises(VerificationError, match="Reviewer notes too long"):
            await review_verification_request(
                request_id=uuid4(),
                reviewer_user_id=uuid4(),
                approved=True,
                reviewer_notes="A" * (MAX_REVIEWER_NOTES_LENGTH + 1),
                db=AsyncMock(),
            )


# ---------------------------------------------------------------------------
# get_verification_request tests
# ---------------------------------------------------------------------------


class TestGetVerificationRequest:
    """Tests for getting a single verification request."""

    @pytest.mark.asyncio
    async def test_returns_request(self) -> None:
        req = _mock_pending_request()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = req
        db.execute.return_value = mock_result

        result = await get_verification_request(req.id, db)
        assert result.id == req.id

    @pytest.mark.asyncio
    async def test_raises_not_found(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(VerificationNotFoundError):
            await get_verification_request(uuid4(), db)


# ---------------------------------------------------------------------------
# list_pending_requests tests
# ---------------------------------------------------------------------------


class TestListPendingRequests:
    """Tests for listing pending requests."""

    @pytest.mark.asyncio
    async def test_returns_list(self) -> None:
        mock_requests = [_mock_pending_request() for _ in range(3)]
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_requests
        db.execute.return_value = mock_result

        result = await list_pending_requests(db)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list(self) -> None:
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        result = await list_pending_requests(db)
        assert result == []


# ---------------------------------------------------------------------------
# get_my_verification_requests tests
# ---------------------------------------------------------------------------


class TestGetMyVerificationRequests:
    """Tests for getting a rescuer's own verification requests."""

    @pytest.mark.asyncio
    async def test_returns_requests(self) -> None:
        profile = _mock_profile()
        mock_requests = [_mock_pending_request(), _mock_pending_request()]
        db = AsyncMock()
        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            result = MagicMock()
            if call_count == 0:
                result.scalar_one_or_none.return_value = profile
            else:
                result.scalars.return_value.all.return_value = mock_requests
            call_count += 1
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        result = await get_my_verification_requests(profile.user_id, db)
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_rejects_no_profile(self) -> None:
        db = _mock_db_no_profile()
        with pytest.raises(RescuerNotFoundError):
            await get_my_verification_requests(uuid4(), db)


# ---------------------------------------------------------------------------
# Error class tests
# ---------------------------------------------------------------------------


class TestErrorClasses:
    """Tests for custom exception classes."""

    def test_verification_error(self) -> None:
        err = VerificationError("bad", details="detail")
        assert err.message == "bad"
        assert err.details == "detail"

    def test_not_found_error(self) -> None:
        err = VerificationNotFoundError("some-id")
        assert err.identifier == "some-id"

    def test_rescuer_not_found_error(self) -> None:
        uid = uuid4()
        err = RescuerNotFoundError(uid)
        assert "Rescuer profile not found" in err.message

    def test_already_verified_error(self) -> None:
        err = AlreadyVerifiedError()
        assert "Already verified" in err.message

    def test_too_many_pending_error(self) -> None:
        err = TooManyPendingRequestsError()
        assert "Too many pending" in err.message

    def test_invalid_transition_error(self) -> None:
        err = InvalidReviewTransitionError("approved")
        assert "approved" in err.details


# ---------------------------------------------------------------------------
# Constants tests
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify service constants."""

    def test_valid_methods(self) -> None:
        assert {"whatsapp", "social", "manual"} == VALID_METHODS

    def test_max_pending_requests(self) -> None:
        assert MAX_PENDING_REQUESTS_PER_RESCUER == 3

    def test_max_evidence_notes(self) -> None:
        assert MAX_EVIDENCE_NOTES_LENGTH == 2000

    def test_max_evidence_url(self) -> None:
        assert MAX_EVIDENCE_URL_LENGTH == 500

    def test_max_reviewer_notes(self) -> None:
        assert MAX_REVIEWER_NOTES_LENGTH == 2000
