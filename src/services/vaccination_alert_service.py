"""Vaccination due-date alert service.

Queries vaccination records to identify upcoming and overdue vaccinations,
returning structured alerts for staff dashboards and notifications.
"""

from datetime import date, timedelta
from enum import StrEnum
from uuid import UUID

import sqlalchemy as sa
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal
from src.db.models.vaccination import Vaccination, VaccineType

# Number of days before a scheduled vaccination to flag it as "upcoming"
ALERT_WINDOW_DAYS = 7


class AlertSeverity(StrEnum):
    """Alert severity levels."""

    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    UPCOMING = "upcoming"


class VaccinationAlertItem(BaseModel):
    """A single vaccination alert."""

    model_config = ConfigDict(from_attributes=True)

    vaccination_id: UUID
    animal_id: UUID
    animal_name: str
    vaccine_name: str
    scheduled_date: date
    days_until_due: int
    severity: str
    dose_number: int


class VaccinationAlertSummary(BaseModel):
    """Summary of all vaccination alerts."""

    overdue: list[VaccinationAlertItem]
    due_today: list[VaccinationAlertItem]
    upcoming: list[VaccinationAlertItem]
    total_overdue: int
    total_due_today: int
    total_upcoming: int


async def get_vaccination_alerts(
    db: AsyncSession,
    *,
    window_days: int = ALERT_WINDOW_DAYS,
    animal_id: UUID | None = None,
) -> VaccinationAlertSummary:
    """Query all scheduled vaccinations that are overdue, due today, or upcoming.

    Args:
        db: Async database session.
        window_days: Number of days ahead to check for upcoming vaccinations.
        animal_id: If provided, filter alerts to a single animal.

    Returns:
        VaccinationAlertSummary with categorized alerts.
    """
    today = date.today()
    window_end = today + timedelta(days=window_days)

    query = (
        sa.select(Vaccination, Animal.name.label("animal_name"), VaccineType.name.label("vaccine_name"))
        .join(Animal, Vaccination.animal_id == Animal.id)
        .join(VaccineType, Vaccination.vaccine_type_id == VaccineType.id)
        .where(
            Vaccination.vaccination_status == "scheduled",
            Vaccination.scheduled_date <= window_end,
        )
        .order_by(Vaccination.scheduled_date.asc())
    )

    if animal_id is not None:
        query = query.where(Vaccination.animal_id == animal_id)

    result = await db.execute(query)
    rows = result.all()

    overdue: list[VaccinationAlertItem] = []
    due_today: list[VaccinationAlertItem] = []
    upcoming: list[VaccinationAlertItem] = []

    for vaccination, animal_name, vaccine_name in rows:
        days_until_due = (vaccination.scheduled_date - today).days

        if days_until_due < 0:
            severity = AlertSeverity.OVERDUE
        elif days_until_due == 0:
            severity = AlertSeverity.DUE_TODAY
        else:
            severity = AlertSeverity.UPCOMING

        alert = VaccinationAlertItem(
            vaccination_id=vaccination.id,
            animal_id=vaccination.animal_id,
            animal_name=animal_name,
            vaccine_name=vaccine_name,
            scheduled_date=vaccination.scheduled_date,
            days_until_due=days_until_due,
            severity=severity,
            dose_number=vaccination.dose_number,
        )

        if severity == AlertSeverity.OVERDUE:
            overdue.append(alert)
        elif severity == AlertSeverity.DUE_TODAY:
            due_today.append(alert)
        else:
            upcoming.append(alert)

    return VaccinationAlertSummary(
        overdue=overdue,
        due_today=due_today,
        upcoming=upcoming,
        total_overdue=len(overdue),
        total_due_today=len(due_today),
        total_upcoming=len(upcoming),
    )
