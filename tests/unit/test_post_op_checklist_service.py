"""Unit tests for post-op checklist generation service."""

from src.services.post_op_checklist_service import (
    DEFAULT_CHECK_INTERVALS,
    STANDARD_CHECK_INTERVALS,
)


class TestCheckIntervalTemplates:
    """Tests for the post-op check schedule templates."""

    def test_spay_has_7_checks(self) -> None:
        assert len(STANDARD_CHECK_INTERVALS["spay"]) == 7

    def test_neuter_has_6_checks(self) -> None:
        assert len(STANDARD_CHECK_INTERVALS["neuter"]) == 6

    def test_emergency_has_most_checks(self) -> None:
        emergency = STANDARD_CHECK_INTERVALS["emergency"]
        assert len(emergency) == 9
        # First check should be at 1 hour
        assert emergency[0][0] == 1

    def test_orthopedic_extends_to_28_days(self) -> None:
        ortho = STANDARD_CHECK_INTERVALS["orthopedic"]
        # Last check at 672 hours = 28 days
        assert ortho[-1][0] == 672

    def test_default_intervals_exist(self) -> None:
        assert len(DEFAULT_CHECK_INTERVALS) >= 3

    def test_all_intervals_are_ascending(self) -> None:
        for surgery_type, intervals in STANDARD_CHECK_INTERVALS.items():
            hours = [h for h, _ in intervals]
            assert hours == sorted(hours), f"{surgery_type} intervals not ascending"

    def test_all_intervals_have_notes(self) -> None:
        for surgery_type, intervals in STANDARD_CHECK_INTERVALS.items():
            for hours, notes in intervals:
                assert isinstance(hours, int), f"{surgery_type}: hours must be int"
                assert len(notes) > 0, f"{surgery_type}: notes must not be empty"

    def test_all_known_surgery_types_have_schedules(self) -> None:
        expected_types = {"spay", "neuter", "mass_removal", "orthopedic", "dental", "emergency"}
        assert expected_types == set(STANDARD_CHECK_INTERVALS.keys())

    def test_default_intervals_ascending(self) -> None:
        hours = [h for h, _ in DEFAULT_CHECK_INTERVALS]
        assert hours == sorted(hours)
