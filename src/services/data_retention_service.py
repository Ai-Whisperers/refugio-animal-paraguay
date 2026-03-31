"""Data retention policy automation service.

Enforces GDPR Article 5(1)(e) storage limitation principle by purging
personal data that is no longer needed for its original purpose.

Retention policies:
  - Expired unused verification tokens: deleted after EXPIRED_TOKEN_RETENTION_DAYS
    (tokens that passed expires_at without being used — the pending action is gone)
  - Used verification tokens: deleted after USED_TOKEN_RETENTION_DAYS
    (tokens that were consumed — kept briefly for audit purposes)

This service does NOT delete audit log entries or anonymized user records.
Audit logs are required for GDPR Article 5(2) accountability and must be
retained for the organisation's legally defined audit period.

Usage (triggered by admin endpoint or external cron):
    result = await run_data_retention(db)
    # result.expired_tokens_deleted: int
    # result.used_tokens_deleted: int
    # result.total_deleted: int
    # result.ran_at: datetime
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.verification_token import VerificationToken

logger = logging.getLogger(__name__)

# ── Retention policy constants ────────────────────────────────────────────────

# Days after expiry to retain unused (never-confirmed) tokens.
# After this period, the token is no longer actionable and holds no value.
EXPIRED_TOKEN_RETENTION_DAYS: int = 30

# Days after a token was used (used_at set) before it is deleted.
# Provides a brief post-use window for debugging and audit correlation.
USED_TOKEN_RETENTION_DAYS: int = 90


# ── Result dataclass ──────────────────────────────────────────────────────────


@dataclass
class DataRetentionResult:
    """Summary of records deleted during a retention run."""

    expired_tokens_deleted: int = 0
    used_tokens_deleted: int = 0
    ran_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total_deleted(self) -> int:
        """Total number of records deleted across all categories."""
        return self.expired_tokens_deleted + self.used_tokens_deleted


# ── Cleanup helpers ───────────────────────────────────────────────────────────


async def purge_expired_unused_tokens(
    db: AsyncSession,
    *,
    retention_days: int = EXPIRED_TOKEN_RETENTION_DAYS,
    now: datetime | None = None,
) -> int:
    """Delete verification tokens that expired without being used.

    A token is eligible when:
      - used_at IS NULL  (never confirmed/consumed)
      - expires_at < now - retention_days  (beyond the retention window)

    Returns the number of tokens deleted.
    """
    cutoff = (now or datetime.now(UTC)) - timedelta(days=retention_days)

    result = await db.execute(
        delete(VerificationToken)
        .where(
            VerificationToken.used_at.is_(None),
            VerificationToken.expires_at < cutoff,
        )
        .returning(VerificationToken.id)
    )
    deleted = len(result.fetchall())
    if deleted:
        logger.info(
            "Data retention: purged %d expired unused verification token(s) "
            "(cutoff: %s, retention_days: %d)",
            deleted,
            cutoff.isoformat(),
            retention_days,
        )
    return deleted


async def purge_used_tokens(
    db: AsyncSession,
    *,
    retention_days: int = USED_TOKEN_RETENTION_DAYS,
    now: datetime | None = None,
) -> int:
    """Delete verification tokens that were used and are beyond the retention window.

    A token is eligible when:
      - used_at IS NOT NULL  (consumed)
      - used_at < now - retention_days  (beyond the retention window)

    Returns the number of tokens deleted.
    """
    cutoff = (now or datetime.now(UTC)) - timedelta(days=retention_days)

    result = await db.execute(
        delete(VerificationToken)
        .where(
            VerificationToken.used_at.is_not(None),
            VerificationToken.used_at < cutoff,
        )
        .returning(VerificationToken.id)
    )
    deleted = len(result.fetchall())
    if deleted:
        logger.info(
            "Data retention: purged %d used verification token(s) "
            "(cutoff: %s, retention_days: %d)",
            deleted,
            cutoff.isoformat(),
            retention_days,
        )
    return deleted


# ── Public entry point ────────────────────────────────────────────────────────


async def run_data_retention(
    db: AsyncSession,
    *,
    expired_token_retention_days: int = EXPIRED_TOKEN_RETENTION_DAYS,
    used_token_retention_days: int = USED_TOKEN_RETENTION_DAYS,
    now: datetime | None = None,
) -> DataRetentionResult:
    """Run all data retention cleanup jobs and return a summary.

    All operations are performed in the same database transaction.
    Call db.commit() after this function if you want the changes persisted.

    Args:
        db: Async SQLAlchemy session.
        expired_token_retention_days: Days after expiry to keep unused tokens.
        used_token_retention_days: Days after use to keep used tokens.
        now: Override for current time (testing only).

    Returns:
        DataRetentionResult with counts of deleted records.
    """
    run_time = now or datetime.now(UTC)
    result = DataRetentionResult(ran_at=run_time)

    result.expired_tokens_deleted = await purge_expired_unused_tokens(
        db,
        retention_days=expired_token_retention_days,
        now=run_time,
    )
    result.used_tokens_deleted = await purge_used_tokens(
        db,
        retention_days=used_token_retention_days,
        now=run_time,
    )

    logger.info(
        "Data retention run complete: %d total record(s) deleted "
        "(expired_tokens=%d, used_tokens=%d)",
        result.total_deleted,
        result.expired_tokens_deleted,
        result.used_tokens_deleted,
    )
    return result


async def count_retention_candidates(
    db: AsyncSession,
    *,
    expired_token_retention_days: int = EXPIRED_TOKEN_RETENTION_DAYS,
    used_token_retention_days: int = USED_TOKEN_RETENTION_DAYS,
    now: datetime | None = None,
) -> dict[str, int]:
    """Count records that would be deleted by a retention run.

    Used by the admin preview endpoint to show pending cleanup without
    actually deleting anything.

    Returns a dict with keys 'expired_tokens', 'used_tokens', 'total'.
    """
    run_time = now or datetime.now(UTC)

    expired_cutoff = run_time - timedelta(days=expired_token_retention_days)
    used_cutoff = run_time - timedelta(days=used_token_retention_days)

    expired_count_result = await db.execute(
        select(func.count()).where(
            VerificationToken.used_at.is_(None),
            VerificationToken.expires_at < expired_cutoff,
        )
    )
    expired_count: int = expired_count_result.scalar_one()

    used_count_result = await db.execute(
        select(func.count()).where(
            VerificationToken.used_at.is_not(None),
            VerificationToken.used_at < used_cutoff,
        )
    )
    used_count: int = used_count_result.scalar_one()

    return {
        "expired_tokens": expired_count,
        "used_tokens": used_count,
        "total": expired_count + used_count,
    }
