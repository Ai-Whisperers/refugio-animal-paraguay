"""Unit tests for vaccination alert service logic."""

from datetime import date, timedelta

from src.services.vaccination_alert_service import (
    ALERT_WINDOW_DAYS,
    AlertSeverity,
    VaccinationAlertItem,
    VaccinationAlertSummary,
)


class TestAlertSeverity:
    """Tests for AlertSeverity enum."""

    def test_values(self) -> None:
        assert AlertSeverity.OVERDUE == "overdue"
        assert AlertSeverity.DUE_TODAY == "due_today"
        assert AlertSeverity.UPCOMING == "upcoming"


class TestVaccinationAlertItem:
    """Tests for VaccinationAlertItem schema."""

    def test_overdue_alert(self) -> None:
        from uuid import uuid4

        alert = VaccinationAlertItem(
            vaccination_id=uuid4(),
            animal_id=uuid4(),
            animal_name="Firulais",
            vaccine_name="Rabies",
            scheduled_date=date.today() - timedelta(days=3),
            days_until_due=-3,
            severity=AlertSeverity.OVERDUE,
            dose_number=1,
        )
        assert alert.severity == "overdue"
        assert alert.days_until_due == -3

    def test_due_today_alert(self) -> None:
        from uuid import uuid4

        alert = VaccinationAlertItem(
            vaccination_id=uuid4(),
            animal_id=uuid4(),
            animal_name="Luna",
            vaccine_name="DHPP",
            scheduled_date=date.today(),
            days_until_due=0,
            severity=AlertSeverity.DUE_TODAY,
            dose_number=2,
        )
        assert alert.severity == "due_today"
        assert alert.days_until_due == 0

    def test_upcoming_alert(self) -> None:
        from uuid import uuid4

        alert = VaccinationAlertItem(
            vaccination_id=uuid4(),
            animal_id=uuid4(),
            animal_name="Max",
            vaccine_name="Bordetella",
            scheduled_date=date.today() + timedelta(days=5),
            days_until_due=5,
            severity=AlertSeverity.UPCOMING,
            dose_number=1,
        )
        assert alert.severity == "upcoming"
        assert alert.days_until_due == 5


class TestVaccinationAlertSummary:
    """Tests for VaccinationAlertSummary schema."""

    def test_empty_summary(self) -> None:
        summary = VaccinationAlertSummary(
            overdue=[],
            due_today=[],
            upcoming=[],
            total_overdue=0,
            total_due_today=0,
            total_upcoming=0,
        )
        assert summary.total_overdue == 0
        assert summary.total_due_today == 0
        assert summary.total_upcoming == 0


class TestAlertWindowConstant:
    """Tests for the default alert window."""

    def test_default_window(self) -> None:
        assert ALERT_WINDOW_DAYS == 7
