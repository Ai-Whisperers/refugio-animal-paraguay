"""Admin API endpoints for data retention policy management.

Endpoints:
  GET  /admin/data-retention/preview  — count records eligible for deletion (dry run)
  POST /admin/data-retention/run      — run the data retention cleanup
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.services.data_retention_service import (
    EXPIRED_TOKEN_RETENTION_DAYS,
    USED_TOKEN_RETENTION_DAYS,
    DataRetentionResult,
    count_retention_candidates,
    run_data_retention,
)

router = APIRouter(
    prefix="/admin/data-retention",
    tags=["admin-data-retention"],
    responses=AUTHENTICATED_RESPONSES,
)


# ── Schemas ──────────────────────────────────────────────────────────────────


class DataRetentionPreviewResponse(BaseModel):
    """Summary of records eligible for deletion without actually deleting them."""

    expired_tokens: int = Field(description="Expired unused verification tokens eligible for deletion")
    used_tokens: int = Field(description="Used verification tokens eligible for deletion")
    total: int = Field(description="Total records eligible for deletion")
    expired_token_retention_days: int = Field(description="Retention period for expired tokens (days)")
    used_token_retention_days: int = Field(description="Retention period for used tokens (days)")


class DataRetentionRunResponse(BaseModel):
    """Result of a completed data retention run."""

    expired_tokens_deleted: int = Field(description="Expired unused verification tokens deleted")
    used_tokens_deleted: int = Field(description="Used verification tokens deleted")
    total_deleted: int = Field(description="Total records deleted")
    ran_at: str = Field(description="ISO timestamp of when the run completed")


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/preview", response_model=DataRetentionPreviewResponse)
async def preview_data_retention(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> DataRetentionPreviewResponse:
    """Dry-run preview — count records eligible for deletion without deleting them.

    Returns counts broken down by category using the current retention policy.
    Use this to assess cleanup volume before triggering a run.
    """
    counts = await count_retention_candidates(db)
    return DataRetentionPreviewResponse(
        expired_tokens=counts["expired_tokens"],
        used_tokens=counts["used_tokens"],
        total=counts["total"],
        expired_token_retention_days=EXPIRED_TOKEN_RETENTION_DAYS,
        used_token_retention_days=USED_TOKEN_RETENTION_DAYS,
    )


@router.post("/run", response_model=DataRetentionRunResponse)
async def run_data_retention_endpoint(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> DataRetentionRunResponse:
    """Execute the data retention cleanup.

    Deletes personal data that has exceeded its retention period:
    - Expired unused verification tokens (password reset, email verify, account deletion)
      older than {EXPIRED_TOKEN_RETENTION_DAYS} days past expiry
    - Used verification tokens older than {USED_TOKEN_RETENTION_DAYS} days past use

    Admin-only. Safe to run repeatedly — idempotent beyond one run per day.
    In production, trigger via a daily cron job or n8n scheduled workflow.
    """
    result: DataRetentionResult = await run_data_retention(db)
    return DataRetentionRunResponse(
        expired_tokens_deleted=result.expired_tokens_deleted,
        used_tokens_deleted=result.used_tokens_deleted,
        total_deleted=result.total_deleted,
        ran_at=result.ran_at.isoformat(),
    )
