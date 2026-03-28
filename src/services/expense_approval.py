"""Service layer for expense approval workflow.

Implements threshold-based approval logic: expenses above the threshold
require admin approval before appearing in financial reports. Expenses
at or below the threshold are auto-approved.
"""

import enum
from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_APPROVAL_THRESHOLD_PYG = 500_000
DEFAULT_APPROVAL_THRESHOLD_EUR = 100_00  # in cents
ESCALATION_DAYS = 5
MAX_BULK_APPROVE = 50


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExpenseApprovalStatus(enum.StrEnum):
    """Status values for the expense approval workflow."""

    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    APPROVED = "approved"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ApprovalThresholdConfig(BaseModel):
    """Configurable approval threshold per currency."""

    threshold_pyg: int = Field(
        default=DEFAULT_APPROVAL_THRESHOLD_PYG,
        ge=0,
        description="Approval threshold in PYG (guaranies)",
    )
    threshold_eur_cents: int = Field(
        default=DEFAULT_APPROVAL_THRESHOLD_EUR,
        ge=0,
        description="Approval threshold in EUR cents",
    )


class ExpenseApprovalRequest(BaseModel):
    """Request to approve or reject an expense."""

    expense_id: UUID
    action: str = Field(..., pattern="^(approve|reject)$")
    admin_id: UUID
    rejection_reason: str | None = None


class ExpenseApprovalResult(BaseModel):
    """Result of an approval action."""

    expense_id: UUID
    previous_status: ExpenseApprovalStatus
    new_status: ExpenseApprovalStatus
    actioned_by: UUID
    actioned_at: str
    rejection_reason: str | None = None


class BulkApprovalRequest(BaseModel):
    """Request to bulk approve multiple expenses."""

    expense_ids: list[UUID] = Field(
        ..., max_length=MAX_BULK_APPROVE, description="Expense IDs to approve"
    )
    admin_id: UUID


class BulkApprovalResult(BaseModel):
    """Result of bulk approval."""

    approved: int
    skipped: int
    errors: list[str]


class PendingExpenseSummary(BaseModel):
    """Summary of a pending expense for admin review."""

    expense_id: UUID
    description: str
    category: str
    amount_cents: int
    currency: str
    expense_date: str
    recorded_by_name: str | None = None
    created_at: str
    days_pending: int


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


def determine_approval_status(
    amount_cents: int,
    currency: str,
    config: ApprovalThresholdConfig | None = None,
) -> ExpenseApprovalStatus:
    """Determine whether an expense requires approval based on threshold.

    Args:
        amount_cents: Expense amount in smallest currency unit.
        currency: ISO 4217 currency code (PYG, EUR, USD).
        config: Optional threshold configuration. Uses defaults if None.

    Returns:
        PENDING if amount exceeds threshold, AUTO_APPROVED otherwise.
    """
    if config is None:
        config = ApprovalThresholdConfig()

    threshold = config.threshold_eur_cents if currency == "EUR" else config.threshold_pyg

    if amount_cents > threshold:
        return ExpenseApprovalStatus.PENDING
    return ExpenseApprovalStatus.AUTO_APPROVED


def approve_expense(
    expense_id: UUID,
    admin_id: UUID,
    current_status: ExpenseApprovalStatus,
) -> ExpenseApprovalResult:
    """Approve a pending expense.

    Args:
        expense_id: The expense to approve.
        admin_id: The admin performing the approval.
        current_status: Current status of the expense.

    Returns:
        ApprovalResult with the status transition.

    Raises:
        ValueError: If expense is not in a reviewable state.
    """
    if current_status not in (
        ExpenseApprovalStatus.PENDING,
        ExpenseApprovalStatus.REJECTED,
    ):
        msg = f"Cannot approve expense in '{current_status.value}' status"
        raise ValueError(msg)

    return ExpenseApprovalResult(
        expense_id=expense_id,
        previous_status=current_status,
        new_status=ExpenseApprovalStatus.APPROVED,
        actioned_by=admin_id,
        actioned_at=datetime.now(UTC).isoformat(),
    )


def reject_expense(
    expense_id: UUID,
    admin_id: UUID,
    current_status: ExpenseApprovalStatus,
    reason: str,
) -> ExpenseApprovalResult:
    """Reject a pending expense.

    Args:
        expense_id: The expense to reject.
        admin_id: The admin performing the rejection.
        current_status: Current status of the expense.
        reason: Rejection reason (required).

    Returns:
        ApprovalResult with the status transition.

    Raises:
        ValueError: If expense is not in a reviewable state or reason missing.
    """
    if current_status != ExpenseApprovalStatus.PENDING:
        msg = f"Cannot reject expense in '{current_status.value}' status"
        raise ValueError(msg)

    if not reason or not reason.strip():
        msg = "Rejection reason is required"
        raise ValueError(msg)

    return ExpenseApprovalResult(
        expense_id=expense_id,
        previous_status=current_status,
        new_status=ExpenseApprovalStatus.REJECTED,
        actioned_by=admin_id,
        actioned_at=datetime.now(UTC).isoformat(),
        rejection_reason=reason.strip(),
    )


def calculate_days_pending(created_at: datetime) -> int:
    """Calculate how many days an expense has been pending."""
    now = datetime.now(UTC)
    delta = now.replace(tzinfo=None) - created_at if created_at.tzinfo is None else now - created_at
    return max(0, delta.days)


def needs_escalation(created_at: datetime) -> bool:
    """Check if a pending expense should trigger an escalation reminder."""
    return calculate_days_pending(created_at) >= ESCALATION_DAYS


def build_approval_notification_subject() -> str:
    """Build the email subject for a new expense approval request."""
    return "Nueva solicitud de aprobacion de gasto"


def build_approval_notification_body(
    description: str,
    amount_cents: int,
    currency: str,
    category: str,
    requester_name: str,
    expense_id: UUID,
    base_url: str = "https://refugioanimal.com.py",
) -> str:
    """Build the email body for a new expense approval request.

    Returns plain text email body in Spanish with approval/rejection links.
    """
    amount_display = f"{amount_cents:,} {currency}"
    return (
        f"Se ha registrado un nuevo gasto que requiere aprobacion:\n\n"
        f"Descripcion: {description}\n"
        f"Monto: {amount_display}\n"
        f"Categoria: {category}\n"
        f"Registrado por: {requester_name}\n\n"
        f"Para revisar: {base_url}/admin/expenses/{expense_id}\n\n"
        f"Aprobar: {base_url}/admin/expenses/{expense_id}/approve\n"
        f"Rechazar: {base_url}/admin/expenses/{expense_id}/reject\n"
    )
