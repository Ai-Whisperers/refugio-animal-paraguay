"""Service layer for automated monthly impact emails.

Handles creation, tracking, and status management of monthly donor
impact email campaigns.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.impact_email_log import (
    VALID_EMAIL_STATUSES,
    EmailStatus,
    ImpactEmailLog,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

MAX_RETRY_COUNT = 3


class ImpactEmailError(Exception):
    """Base error for impact email operations."""


class EmailLogNotFoundError(ImpactEmailError):
    """Raised when an email log does not exist."""


class DuplicateEmailError(ImpactEmailError):
    """Raised when an email for this donor/period already exists."""


class InvalidEmailError(ImpactEmailError):
    """Raised when email validation fails."""


async def create_email_log(
    db: AsyncSession,
    donor_id: UUID,
    email_address: str,
    subject: str,
    report_month: int,
    report_year: int,
    donation_total: float,
    currency: str = "PYG",
    animals_rescued: int = 0,
    animals_adopted: int = 0,
    castrations_funded: int = 0,
    medical_treatments: int = 0,
) -> dict:
    """Create an impact email log entry."""
    if not email_address or not email_address.strip():
        raise InvalidEmailError("Email address is required")
    if report_month < 1 or report_month > 12:
        raise InvalidEmailError(f"Invalid month {report_month}, must be 1-12")
    if report_year < 2020:
        raise InvalidEmailError(f"Invalid year {report_year}")
    if donation_total < 0:
        raise InvalidEmailError("Donation total cannot be negative")

    # Check for duplicate
    existing = await db.execute(
        select(func.count())
        .select_from(ImpactEmailLog)
        .where(
            ImpactEmailLog.donor_id == donor_id,
            ImpactEmailLog.report_year == report_year,
            ImpactEmailLog.report_month == report_month,
        )
    )
    if existing.scalar_one() > 0:
        raise DuplicateEmailError(
            f"Impact email for donor {donor_id} period {report_year}-{report_month:02d} already exists"
        )

    log = ImpactEmailLog(
        donor_id=donor_id,
        email_address=email_address.strip(),
        subject=subject,
        report_month=report_month,
        report_year=report_year,
        donation_total=donation_total,
        currency=currency,
        animals_rescued=animals_rescued,
        animals_adopted=animals_adopted,
        castrations_funded=castrations_funded,
        medical_treatments=medical_treatments,
        status=EmailStatus.PENDING.value,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)

    return _log_to_dict(log)


async def get_email_log(db: AsyncSession, log_id: UUID) -> dict:
    """Get an email log by ID."""
    result = await db.execute(select(ImpactEmailLog).where(ImpactEmailLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise EmailLogNotFoundError(f"Email log {log_id} not found")
    return _log_to_dict(log)


async def list_email_logs(
    db: AsyncSession,
    donor_id: UUID | None = None,
    status_filter: str | None = None,
    report_year: int | None = None,
    report_month: int | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
    offset: int = 0,
) -> dict:
    """List email logs with optional filters."""
    base_query = select(ImpactEmailLog)

    if donor_id is not None:
        base_query = base_query.where(ImpactEmailLog.donor_id == donor_id)
    if status_filter is not None:
        base_query = base_query.where(ImpactEmailLog.status == status_filter)
    if report_year is not None:
        base_query = base_query.where(ImpactEmailLog.report_year == report_year)
    if report_month is not None:
        base_query = base_query.where(ImpactEmailLog.report_month == report_month)

    count_query = select(func.count()).select_from(base_query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.order_by(ImpactEmailLog.created_at.desc()).limit(limit).offset(offset)
    )
    logs = list(result.scalars().all())

    return {
        "email_logs": [_log_to_dict(log) for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


async def update_email_status(
    db: AsyncSession,
    log_id: UUID,
    new_status: str,
    failure_reason: str | None = None,
) -> dict:
    """Update the status of an email log."""
    result = await db.execute(select(ImpactEmailLog).where(ImpactEmailLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise EmailLogNotFoundError(f"Email log {log_id} not found")

    if new_status not in VALID_EMAIL_STATUSES:
        raise InvalidEmailError(f"Invalid status '{new_status}'")

    now = datetime.now(UTC)
    log.status = new_status

    if new_status == EmailStatus.SENT:
        log.sent_at = now
    elif new_status == EmailStatus.OPENED:
        log.opened_at = now
    elif (new_status == EmailStatus.FAILED and failure_reason) or (
        new_status == EmailStatus.BOUNCED and failure_reason
    ):
        log.failure_reason = failure_reason

    await db.flush()
    await db.refresh(log)

    return _log_to_dict(log)


async def increment_retry(db: AsyncSession, log_id: UUID) -> dict:
    """Increment retry count and reset to pending if under max retries."""
    result = await db.execute(select(ImpactEmailLog).where(ImpactEmailLog.id == log_id))
    log = result.scalar_one_or_none()
    if log is None:
        raise EmailLogNotFoundError(f"Email log {log_id} not found")

    if log.retry_count >= MAX_RETRY_COUNT:
        raise InvalidEmailError(f"Max retry count ({MAX_RETRY_COUNT}) reached for email {log_id}")

    log.retry_count += 1
    log.status = EmailStatus.PENDING.value
    log.failure_reason = None

    await db.flush()
    await db.refresh(log)

    return _log_to_dict(log)


async def get_campaign_stats(
    db: AsyncSession,
    report_year: int,
    report_month: int,
) -> dict:
    """Get statistics for a monthly email campaign."""
    base_query = select(ImpactEmailLog).where(
        ImpactEmailLog.report_year == report_year,
        ImpactEmailLog.report_month == report_month,
    )

    total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = total_result.scalar_one()

    stats: dict[str, int] = {}
    for status_val in VALID_EMAIL_STATUSES:
        status_query = base_query.where(ImpactEmailLog.status == status_val)
        count_result = await db.execute(select(func.count()).select_from(status_query.subquery()))
        stats[status_val] = count_result.scalar_one()

    return {
        "report_year": report_year,
        "report_month": report_month,
        "total": total,
        "by_status": stats,
    }


def _log_to_dict(log: ImpactEmailLog) -> dict:
    """Convert an ImpactEmailLog to a dict."""
    return {
        "id": log.id,
        "donor_id": log.donor_id,
        "email_address": log.email_address,
        "subject": log.subject,
        "report_month": log.report_month,
        "report_year": log.report_year,
        "donation_total": log.donation_total,
        "currency": log.currency,
        "animals_rescued": log.animals_rescued,
        "animals_adopted": log.animals_adopted,
        "castrations_funded": log.castrations_funded,
        "medical_treatments": log.medical_treatments,
        "status": log.status,
        "sent_at": log.sent_at,
        "opened_at": log.opened_at,
        "failure_reason": log.failure_reason,
        "retry_count": log.retry_count,
        "created_at": log.created_at,
    }
