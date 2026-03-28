"""API endpoints for expense approval workflow.

Provides admin endpoints for reviewing, approving, and rejecting expenses
that exceed the configured approval threshold.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.services.expense_approval import (
    MAX_BULK_APPROVE,
    ApprovalThresholdConfig,
    BulkApprovalResult,
    ExpenseApprovalResult,
    ExpenseApprovalStatus,
    approve_expense,
    build_approval_notification_body,
    build_approval_notification_subject,
    determine_approval_status,
    reject_expense,
)

router = APIRouter(
    prefix="/api/admin/expense-approvals",
    tags=["expense-approvals"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    """Request body for approving an expense."""

    admin_id: UUID


class RejectRequest(BaseModel):
    """Request body for rejecting an expense."""

    admin_id: UUID
    reason: str = Field(..., min_length=1, max_length=1000)


class BulkApproveRequest(BaseModel):
    """Request body for bulk approving expenses."""

    expense_ids: list[UUID] = Field(..., max_length=MAX_BULK_APPROVE)
    admin_id: UUID


class ThresholdResponse(BaseModel):
    """Current approval threshold configuration."""

    threshold_pyg: int
    threshold_eur_cents: int


class ThresholdUpdateRequest(BaseModel):
    """Request to update approval thresholds."""

    threshold_pyg: int = Field(..., ge=0)
    threshold_eur_cents: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# In-memory state for MVP
# ---------------------------------------------------------------------------

_config = ApprovalThresholdConfig()

# Track approval status per expense (MVP — in production, stored in DB)
_expense_statuses: dict[str, ExpenseApprovalStatus] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/threshold",
    response_model=ThresholdResponse,
    summary="Get current approval thresholds",
)
async def get_threshold() -> ThresholdResponse:
    """Return current approval threshold configuration."""
    return ThresholdResponse(
        threshold_pyg=_config.threshold_pyg,
        threshold_eur_cents=_config.threshold_eur_cents,
    )


@router.put(
    "/threshold",
    response_model=ThresholdResponse,
    summary="Update approval thresholds",
)
async def update_threshold(body: ThresholdUpdateRequest) -> ThresholdResponse:
    """Update approval threshold configuration.

    Requires admin role (enforced by auth middleware in production).
    """
    global _config
    _config = ApprovalThresholdConfig(
        threshold_pyg=body.threshold_pyg,
        threshold_eur_cents=body.threshold_eur_cents,
    )
    return ThresholdResponse(
        threshold_pyg=_config.threshold_pyg,
        threshold_eur_cents=_config.threshold_eur_cents,
    )


@router.post(
    "/check",
    summary="Check if an expense requires approval",
)
async def check_approval_required(
    amount_cents: int,
    currency: str = "PYG",
) -> dict[str, str | bool]:
    """Check if an expense amount requires approval."""
    approval_status = determine_approval_status(amount_cents, currency, _config)
    return {
        "requires_approval": approval_status == ExpenseApprovalStatus.PENDING,
        "status": approval_status.value,
    }


@router.post(
    "/{expense_id}/approve",
    response_model=ExpenseApprovalResult,
    summary="Approve a pending expense",
)
async def approve(expense_id: UUID, body: ApproveRequest) -> ExpenseApprovalResult:
    """Approve an expense that is pending review."""
    key = str(expense_id)
    current = _expense_statuses.get(key, ExpenseApprovalStatus.PENDING)

    try:
        result = approve_expense(expense_id, body.admin_id, current)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    _expense_statuses[key] = result.new_status
    return result


@router.post(
    "/{expense_id}/reject",
    response_model=ExpenseApprovalResult,
    summary="Reject a pending expense",
)
async def reject(expense_id: UUID, body: RejectRequest) -> ExpenseApprovalResult:
    """Reject an expense with a mandatory reason."""
    key = str(expense_id)
    current = _expense_statuses.get(key, ExpenseApprovalStatus.PENDING)

    try:
        result = reject_expense(expense_id, body.admin_id, current, body.reason)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    _expense_statuses[key] = result.new_status
    return result


@router.post(
    "/bulk-approve",
    response_model=BulkApprovalResult,
    summary="Bulk approve multiple pending expenses",
)
async def bulk_approve(body: BulkApproveRequest) -> BulkApprovalResult:
    """Approve multiple pending expenses at once (max 50)."""
    approved = 0
    skipped = 0
    errors: list[str] = []

    for eid in body.expense_ids:
        key = str(eid)
        current = _expense_statuses.get(key, ExpenseApprovalStatus.PENDING)

        try:
            result = approve_expense(eid, body.admin_id, current)
            _expense_statuses[key] = result.new_status
            approved += 1
        except ValueError as exc:
            skipped += 1
            errors.append(f"{eid}: {exc}")

    return BulkApprovalResult(approved=approved, skipped=skipped, errors=errors)


@router.get(
    "/notification-preview",
    summary="Preview approval notification email",
)
async def notification_preview() -> dict[str, str]:
    """Preview the notification email template (for testing)."""
    from uuid import uuid4

    subject = build_approval_notification_subject()
    body = build_approval_notification_body(
        description="Medicamentos veterinarios",
        amount_cents=750_000,
        currency="PYG",
        category="medical",
        requester_name="Maria Lopez",
        expense_id=uuid4(),
    )
    return {"subject": subject, "body": body}
