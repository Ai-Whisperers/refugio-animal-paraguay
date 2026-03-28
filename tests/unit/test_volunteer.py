"""Unit tests for volunteer registration API (RAP-640).

Tests the schemas, validation, and business logic of volunteer endpoints
without requiring a live database.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.api.volunteer import (
    VolunteerApplyRequest,
    VolunteerReviewRequest,
    VolunteerUpdateRequest,
    _build_profile_response,
)
from src.db.models.volunteer_profile import (
    VOLUNTEER_SKILL_OPTIONS,
    VolunteerAvailability,
    VolunteerProfile,
    VolunteerStatus,
)

# ---------------------------------------------------------------------------
# VolunteerStatus
# ---------------------------------------------------------------------------


class TestVolunteerStatus:
    def test_valid_values_are_strings(self):
        assert VolunteerStatus.PENDING == "pending"
        assert VolunteerStatus.APPROVED == "approved"
        assert VolunteerStatus.REJECTED == "rejected"
        assert VolunteerStatus.INACTIVE == "inactive"


# ---------------------------------------------------------------------------
# VolunteerApplyRequest schema validation
# ---------------------------------------------------------------------------


class TestVolunteerApplyRequest:
    def test_minimal_valid_request(self):
        req = VolunteerApplyRequest(
            motivation="Me gustan mucho los animales y quiero ayudar al refugio.",
        )
        assert req.motivation.startswith("Me gustan")
        assert req.skills == []
        assert req.availability == []
        assert req.hours_per_week is None

    def test_full_valid_request(self):
        req = VolunteerApplyRequest(
            motivation="Tengo experiencia con animales rescatados y quiero colaborar activamente.",
            skills=["animal_care", "photography"],
            availability=["weekend_mornings", "flexible"],
            hours_per_week=8,
            emergency_contact_name="Ana Ramirez",
            emergency_contact_phone="+595981234567",
        )
        assert req.hours_per_week == 8
        assert "animal_care" in req.skills
        assert req.emergency_contact_name == "Ana Ramirez"

    def test_motivation_too_short_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            VolunteerApplyRequest(motivation="Corto")
        errors = exc_info.value.errors()
        assert any("motivation" in str(e) for e in errors)

    def test_motivation_minimum_length_exactly_20(self):
        req = VolunteerApplyRequest(motivation="A" * 20)
        assert len(req.motivation) == 20

    def test_hours_per_week_zero_raises(self):
        with pytest.raises(ValidationError):
            VolunteerApplyRequest(
                motivation="A" * 25,
                hours_per_week=0,
            )

    def test_hours_per_week_41_raises(self):
        with pytest.raises(ValidationError):
            VolunteerApplyRequest(
                motivation="A" * 25,
                hours_per_week=41,
            )

    def test_hours_per_week_boundary_values_valid(self):
        req_min = VolunteerApplyRequest(motivation="A" * 25, hours_per_week=1)
        assert req_min.hours_per_week == 1

        req_max = VolunteerApplyRequest(motivation="A" * 25, hours_per_week=40)
        assert req_max.hours_per_week == 40

    def test_skills_accept_any_list(self):
        req = VolunteerApplyRequest(
            motivation="A" * 25,
            skills=["animal_care", "transport_driving", "photography"],
        )
        assert len(req.skills) == 3

    def test_empty_skills_and_availability_default(self):
        req = VolunteerApplyRequest(motivation="A" * 25)
        assert req.skills == []
        assert req.availability == []


# ---------------------------------------------------------------------------
# VolunteerUpdateRequest
# ---------------------------------------------------------------------------


class TestVolunteerUpdateRequest:
    def test_all_fields_optional(self):
        req = VolunteerUpdateRequest()
        assert req.motivation is None
        assert req.skills is None
        assert req.availability is None
        assert req.hours_per_week is None

    def test_motivation_too_short_raises(self):
        with pytest.raises(ValidationError):
            VolunteerUpdateRequest(motivation="Short")

    def test_valid_partial_update(self):
        req = VolunteerUpdateRequest(
            skills=["social_media", "admin_office"],
            hours_per_week=4,
        )
        assert req.skills == ["social_media", "admin_office"]
        assert req.hours_per_week == 4
        assert req.motivation is None


# ---------------------------------------------------------------------------
# VolunteerReviewRequest
# ---------------------------------------------------------------------------


class TestVolunteerReviewRequest:
    def test_approved_without_reason(self):
        req = VolunteerReviewRequest(decision=VolunteerStatus.APPROVED)
        assert req.decision == VolunteerStatus.APPROVED
        assert req.rejection_reason is None

    def test_rejected_with_reason(self):
        req = VolunteerReviewRequest(
            decision=VolunteerStatus.REJECTED,
            rejection_reason="No cumple los requisitos de edad.",
        )
        assert req.rejection_reason is not None

    def test_invalid_decision_raises(self):
        with pytest.raises(ValidationError):
            VolunteerReviewRequest(decision="unknown_status")


# ---------------------------------------------------------------------------
# VOLUNTEER_SKILL_OPTIONS constant
# ---------------------------------------------------------------------------


class TestVolunteerSkillOptions:
    def test_contains_expected_skills(self):
        expected = {
            "animal_care",
            "veterinary_assistance",
            "photography",
            "social_media",
            "transport_driving",
        }
        assert expected.issubset(VOLUNTEER_SKILL_OPTIONS)

    def test_is_frozenset(self):
        assert isinstance(VOLUNTEER_SKILL_OPTIONS, frozenset)

    def test_minimum_skill_count(self):
        assert len(VOLUNTEER_SKILL_OPTIONS) >= 10


# ---------------------------------------------------------------------------
# VolunteerAvailability enum
# ---------------------------------------------------------------------------


class TestVolunteerAvailability:
    def test_valid_values(self):
        assert VolunteerAvailability.WEEKDAY_MORNINGS == "weekday_mornings"
        assert VolunteerAvailability.FLEXIBLE == "flexible"
        assert VolunteerAvailability.WEEKEND_AFTERNOONS == "weekend_afternoons"


# ---------------------------------------------------------------------------
# _build_profile_response helper
# ---------------------------------------------------------------------------


class TestBuildProfileResponse:
    def _make_profile(self, **overrides):
        from datetime import UTC, datetime
        from unittest.mock import MagicMock

        profile = MagicMock(spec=VolunteerProfile)
        profile.id = overrides.get("id", uuid4())
        profile.user_id = overrides.get("user_id", uuid4())
        profile.motivation = overrides.get(
            "motivation", "Quiero ayudar a los animales del refugio."
        )
        profile.skills = overrides.get("skills", ["animal_care"])
        profile.availability = overrides.get("availability", ["flexible"])
        profile.hours_per_week = overrides.get("hours_per_week")
        profile.emergency_contact_name = overrides.get("emergency_contact_name")
        profile.emergency_contact_phone = overrides.get("emergency_contact_phone")
        profile.status = overrides.get("status", VolunteerStatus.PENDING)
        profile.rejection_reason = overrides.get("rejection_reason")
        profile.total_hours_logged = overrides.get("total_hours_logged", 0)
        profile.created_at = overrides.get("created_at", datetime.now(UTC))
        return profile

    def _make_user(self, **overrides):
        from unittest.mock import MagicMock

        from src.db.models.user import User

        user = MagicMock(spec=User)
        user.id = overrides.get("id", uuid4())
        user.full_name = overrides.get("full_name", "Juan Perez")
        user.email = overrides.get("email", "juan@example.com")
        user.role = overrides.get("role", "volunteer")
        return user

    def test_builds_correct_structure(self):
        profile = self._make_profile()
        user = self._make_user()
        result = _build_profile_response(profile, user)

        assert result["user_id"] == profile.user_id
        assert result["email"] == user.email
        assert result["full_name"] == user.full_name
        assert result["motivation"] == profile.motivation
        assert result["skills"] == ["animal_care"]
        assert result["status"] == VolunteerStatus.PENDING

    def test_handles_none_user(self):
        profile = self._make_profile()
        result = _build_profile_response(profile, None)
        assert result["full_name"] is None
        assert result["email"] == ""

    def test_total_hours_logged_as_float(self):
        profile = self._make_profile(total_hours_logged=12)
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert isinstance(result["total_hours_logged"], float)
        assert result["total_hours_logged"] == 12.0

    def test_none_skills_returns_empty_list(self):
        profile = self._make_profile(skills=None)
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert result["skills"] == []

    def test_none_availability_returns_empty_list(self):
        profile = self._make_profile(availability=None)
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert result["availability"] == []


# ---------------------------------------------------------------------------
# RAP-641: VolunteerProfileUpdateRequest schema validation
# ---------------------------------------------------------------------------


class TestVolunteerProfileUpdateRequest:
    """Tests for the new skills/availability/bio update schema (RAP-641)."""

    def test_empty_request_is_valid(self):
        from src.api.volunteer import VolunteerProfileUpdateRequest

        req = VolunteerProfileUpdateRequest()
        assert req.bio is None
        assert req.skills is None
        assert req.availability is None
        assert req.hours_per_week is None
        assert req.languages_spoken is None

    def test_full_valid_request(self):
        from src.api.volunteer import VolunteerProfileUpdateRequest

        req = VolunteerProfileUpdateRequest(
            bio="Soy amante de los animales y tengo experiencia con perros rescatados.",
            skills=["animal_care", "photography"],
            availability=["weekend_mornings", "flexible"],
            hours_per_week=6,
            languages_spoken=["Español", "Inglés"],
        )
        assert req.bio is not None
        assert "animal_care" in req.skills
        assert req.hours_per_week == 6
        assert "Español" in req.languages_spoken

    def test_bio_max_length_enforced(self):
        from pydantic import ValidationError
        from src.api.volunteer import VolunteerProfileUpdateRequest

        with pytest.raises(ValidationError):
            VolunteerProfileUpdateRequest(bio="x" * 501)

    def test_bio_500_chars_is_valid(self):
        from src.api.volunteer import VolunteerProfileUpdateRequest

        req = VolunteerProfileUpdateRequest(bio="a" * 500)
        assert req.bio is not None
        assert len(req.bio) == 500

    def test_hours_per_week_min_1(self):
        from pydantic import ValidationError
        from src.api.volunteer import VolunteerProfileUpdateRequest

        with pytest.raises(ValidationError):
            VolunteerProfileUpdateRequest(hours_per_week=0)

    def test_hours_per_week_max_40(self):
        from pydantic import ValidationError
        from src.api.volunteer import VolunteerProfileUpdateRequest

        with pytest.raises(ValidationError):
            VolunteerProfileUpdateRequest(hours_per_week=41)

    def test_hours_per_week_boundary_valid(self):
        from src.api.volunteer import VolunteerProfileUpdateRequest

        req1 = VolunteerProfileUpdateRequest(hours_per_week=1)
        req2 = VolunteerProfileUpdateRequest(hours_per_week=40)
        assert req1.hours_per_week == 1
        assert req2.hours_per_week == 40


# ---------------------------------------------------------------------------
# RAP-641: VolunteerProfileOptions schema
# ---------------------------------------------------------------------------


class TestVolunteerProfileOptions:
    def test_options_structure(self):
        from src.api.volunteer import VolunteerProfileOptions

        opts = VolunteerProfileOptions(
            skills=["animal_care", "photography"],
            availability=["weekday_mornings", "flexible"],
        )
        assert "animal_care" in opts.skills
        assert "flexible" in opts.availability


# ---------------------------------------------------------------------------
# RAP-641: _build_profile_response includes new fields
# ---------------------------------------------------------------------------


class TestBuildProfileResponseRAP641:
    def _make_profile(self, **overrides):
        from unittest.mock import MagicMock

        profile = MagicMock(spec=VolunteerProfile)
        profile.id = overrides.get("id", uuid4())
        profile.user_id = overrides.get("user_id", uuid4())
        profile.motivation = overrides.get("motivation", "Me gustan los animales y quiero ayudar.")
        profile.bio = overrides.get("bio", "Voluntaria con experiencia en cuidado felino.")
        profile.skills = overrides.get("skills", ["animal_care"])
        profile.availability = overrides.get("availability", ["weekend_mornings"])
        profile.hours_per_week = overrides.get("hours_per_week", 5)
        profile.languages_spoken = overrides.get("languages_spoken", ["Español", "Guaraní"])
        profile.emergency_contact_name = overrides.get("emergency_contact_name")
        profile.emergency_contact_phone = overrides.get("emergency_contact_phone")
        profile.status = overrides.get("status", VolunteerStatus.APPROVED)
        profile.rejection_reason = overrides.get("rejection_reason")
        profile.reviewed_by = overrides.get("reviewed_by")
        profile.reviewed_at = overrides.get("reviewed_at")
        profile.total_hours_logged = overrides.get("total_hours_logged", 0)
        profile.created_at = overrides.get("created_at")
        profile.updated_at = overrides.get("updated_at")
        return profile

    def _make_user(self, **overrides):
        from unittest.mock import MagicMock

        from src.db.models.user import User

        user = MagicMock(spec=User)
        user.id = overrides.get("id", uuid4())
        user.full_name = overrides.get("full_name", "María González")
        user.email = overrides.get("email", "maria@example.com")
        return user

    def test_bio_included_in_response(self):
        profile = self._make_profile(bio="Voluntaria con años de experiencia.")
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert result["bio"] == "Voluntaria con años de experiencia."

    def test_bio_none_is_preserved(self):
        profile = self._make_profile(bio=None)
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert result["bio"] is None

    def test_languages_spoken_included(self):
        profile = self._make_profile(languages_spoken=["Español", "Inglés"])
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert result["languages_spoken"] == ["Español", "Inglés"]

    def test_languages_spoken_none_returns_empty_list(self):
        profile = self._make_profile(languages_spoken=None)
        user = self._make_user()
        result = _build_profile_response(profile, user)
        assert result["languages_spoken"] == []


# ---------------------------------------------------------------------------
# RAP-643: get_volunteer_profile_by_id endpoint
# ---------------------------------------------------------------------------


class TestGetVolunteerProfileById:
    """Unit tests for the GET /api/staff/volunteers/{id} endpoint (RAP-643)."""

    def _make_profile(self, **overrides):
        from datetime import UTC, datetime
        from unittest.mock import MagicMock

        profile = MagicMock(spec=VolunteerProfile)
        profile.id = overrides.get("id", uuid4())
        profile.user_id = overrides.get("user_id", uuid4())
        profile.motivation = overrides.get("motivation", "Quiero ayudar.")
        profile.bio = overrides.get("bio")
        profile.skills = overrides.get("skills", ["animal_care"])
        profile.availability = overrides.get("availability", ["flexible"])
        profile.hours_per_week = overrides.get("hours_per_week", 10)
        profile.languages_spoken = overrides.get("languages_spoken", ["Español"])
        profile.emergency_contact_name = overrides.get("emergency_contact_name", "Maria")
        profile.emergency_contact_phone = overrides.get("emergency_contact_phone", "+595999000")
        profile.status = overrides.get("status", VolunteerStatus.PENDING)
        profile.rejection_reason = overrides.get("rejection_reason")
        profile.total_hours_logged = overrides.get("total_hours_logged", 0)
        profile.created_at = overrides.get("created_at", datetime.now(UTC))
        return profile

    def test_build_profile_response_includes_all_required_fields(self):
        """Returned dict contains all fields expected by VolunteerProfileResponse."""
        from unittest.mock import MagicMock

        from src.db.models.user import User

        profile = self._make_profile()
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.full_name = "Ana Garcia"
        user.email = "ana@example.com"

        result = _build_profile_response(profile, user)

        required_fields = {
            "id",
            "user_id",
            "full_name",
            "email",
            "motivation",
            "bio",
            "skills",
            "availability",
            "hours_per_week",
            "languages_spoken",
            "emergency_contact_name",
            "emergency_contact_phone",
            "status",
            "rejection_reason",
            "total_hours_logged",
            "created_at",
        }
        assert required_fields.issubset(result.keys())

    def test_build_profile_response_status_matches_profile(self):
        """Status in response matches the profile's status."""
        from unittest.mock import MagicMock

        from src.db.models.user import User

        profile = self._make_profile(status=VolunteerStatus.APPROVED)
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.full_name = "Jose Lopez"
        user.email = "jose@example.com"

        result = _build_profile_response(profile, user)

        assert result["status"] == VolunteerStatus.APPROVED

    def test_build_profile_response_rejected_includes_reason(self):
        """Rejection reason is preserved for rejected applications."""
        from unittest.mock import MagicMock

        from src.db.models.user import User

        reason = "No cumple con los requisitos minimos de experiencia."
        profile = self._make_profile(
            status=VolunteerStatus.REJECTED,
            rejection_reason=reason,
        )
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.full_name = "Pedro Ruiz"
        user.email = "pedro@example.com"

        result = _build_profile_response(profile, user)

        assert result["rejection_reason"] == reason
