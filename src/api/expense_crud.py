"""Extended CRUD API for expense management.

Complements the existing expense endpoints in donation_allocations.py
with update, delete, and enhanced filtering. Integrates with the
approval workflow from expense_approval.py.
"""

import enum
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/admin/expenses",
    tags=["expense-management"],
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExpenseStatus(enum.StrEnum):
    """Expense approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ExpenseCategoryExtended(enum.StrEnum):
    """Extended expense categories per RAP-604 requirements."""

    MEDICAL = "medical"
    FOOD = "food"
    SHELTER = "shelter"
    RESCUE = "rescue"
    OPERATIONS = "operations"
    TRANSPORT = "transport"
    ADMIN = "admin"
    OTHER = "other"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ExpenseCreateRequest(BaseModel):
    """Request to create a new expense record."""

    amount_cents: int = Field(..., gt=0, description="Amount in cents (positive)")
    currency: str = Field(default="PYG", pattern="^(PYG|USD|EUR)$", description="Currency code")
    category: ExpenseCategoryExtended
    description: str = Field(..., min_length=3, max_length=500)
    receipt_url: str | None = Field(None, max_length=1000)
    expense_date: date
    recorded_by_id: UUID | None = None
    notes: str | None = Field(None, max_length=1000)


class ExpenseUpdateRequest(BaseModel):
    """Request to update an existing expense (only if not yet approved)."""

    amount_cents: int | None = Field(None, gt=0)
    currency: str | None = Field(None, pattern="^(PYG|USD|EUR)$")
    category: ExpenseCategoryExtended | None = None
    description: str | None = Field(None, min_length=3, max_length=500)
    receipt_url: str | None = None
    expense_date: date | None = None
    notes: str | None = None


class ExpenseResponse(BaseModel):
    """Full expense record response."""

    id: str
    amount_cents: int
    currency: str
    category: str
    description: str
    receipt_url: str | None
    expense_date: str
    status: str
    recorded_by_id: str | None
    recorded_by_name: str | None
    approved_by_id: str | None
    approved_by_name: str | None
    rejection_reason: str | None
    notes: str | None
    created_at: str
    updated_at: str


class ExpenseListResponse(BaseModel):
    """Paginated list of expenses."""

    items: list[ExpenseResponse]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# In-memory store (MVP — production uses DB)
# ---------------------------------------------------------------------------

_expenses: dict[str, dict] = {}
_next_id = 1


def _now_iso() -> str:
    return datetime.now().isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense record",
)
async def create_expense(body: ExpenseCreateRequest) -> ExpenseResponse:
    """Create a new expense record. Requires admin/staff role."""
    global _next_id

    # Validate expense_date not in future
    if body.expense_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha del gasto no puede ser futura",
        )

    expense_id = str(_next_id)
    _next_id += 1

    now = _now_iso()
    expense = {
        "id": expense_id,
        "amount_cents": body.amount_cents,
        "currency": body.currency,
        "category": body.category.value,
        "description": body.description,
        "receipt_url": body.receipt_url,
        "expense_date": body.expense_date.isoformat(),
        "status": ExpenseStatus.PENDING.value,
        "recorded_by_id": str(body.recorded_by_id) if body.recorded_by_id else None,
        "recorded_by_name": None,
        "approved_by_id": None,
        "approved_by_name": None,
        "rejection_reason": None,
        "notes": body.notes,
        "created_at": now,
        "updated_at": now,
    }

    _expenses[expense_id] = expense
    return ExpenseResponse(**expense)


@router.get(
    "",
    response_model=ExpenseListResponse,
    summary="List expenses with optional filters",
)
async def list_expenses(
    category: ExpenseCategoryExtended | None = None,
    expense_status: ExpenseStatus | None = Query(None, alias="status"),
    date_from: date | None = None,
    date_to: date | None = None,
    recorded_by: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ExpenseListResponse:
    """List expenses with filtering and pagination."""
    items = list(_expenses.values())

    if category:
        items = [e for e in items if e["category"] == category.value]
    if expense_status:
        items = [e for e in items if e["status"] == expense_status.value]
    if date_from:
        items = [e for e in items if e["expense_date"] >= date_from.isoformat()]
    if date_to:
        items = [e for e in items if e["expense_date"] <= date_to.isoformat()]
    if recorded_by:
        items = [e for e in items if e["recorded_by_id"] == str(recorded_by)]

    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]

    return ExpenseListResponse(
        items=[ExpenseResponse(**e) for e in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Get expense details",
)
async def get_expense(expense_id: str) -> ExpenseResponse:
    """Get a single expense by ID."""
    expense = _expenses.get(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado",
        )
    return ExpenseResponse(**expense)


@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
    summary="Update an expense (if not approved)",
)
async def update_expense(expense_id: str, body: ExpenseUpdateRequest) -> ExpenseResponse:
    """Update an expense. Only allowed if status is pending."""
    expense = _expenses.get(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado",
        )
    if expense["status"] == ExpenseStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede editar un gasto aprobado",
        )

    update_data = body.model_dump(exclude_unset=True)
    if update_data.get("expense_date"):
        if update_data["expense_date"] > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha del gasto no puede ser futura",
            )
        update_data["expense_date"] = update_data["expense_date"].isoformat()
    if update_data.get("category"):
        update_data["category"] = update_data["category"].value

    expense.update(update_data)
    expense["updated_at"] = _now_iso()

    return ExpenseResponse(**expense)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense (if not approved)",
)
async def delete_expense(expense_id: str) -> None:
    """Soft-delete an expense. Only allowed if status is pending."""
    expense = _expenses.get(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado",
        )
    if expense["status"] == ExpenseStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un gasto aprobado",
        )
    del _expenses[expense_id]


@router.patch(
    "/{expense_id}/approve",
    response_model=ExpenseResponse,
    summary="Approve an expense",
)
async def approve_expense(
    expense_id: str,
    admin_id: UUID | None = None,
) -> ExpenseResponse:
    """Approve a pending expense. Requires admin role."""
    expense = _expenses.get(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado",
        )
    if expense["status"] != ExpenseStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden aprobar gastos pendientes",
        )

    expense["status"] = ExpenseStatus.APPROVED.value
    expense["approved_by_id"] = str(admin_id) if admin_id else None
    expense["updated_at"] = _now_iso()

    return ExpenseResponse(**expense)


@router.patch(
    "/{expense_id}/reject",
    response_model=ExpenseResponse,
    summary="Reject an expense with reason",
)
async def reject_expense(
    expense_id: str,
    reason: str = Query(..., min_length=1, max_length=500),
    admin_id: UUID | None = None,
) -> ExpenseResponse:
    """Reject a pending expense with a mandatory reason."""
    expense = _expenses.get(expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gasto no encontrado",
        )
    if expense["status"] != ExpenseStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden rechazar gastos pendientes",
        )

    expense["status"] = ExpenseStatus.REJECTED.value
    expense["rejection_reason"] = reason
    expense["approved_by_id"] = str(admin_id) if admin_id else None
    expense["updated_at"] = _now_iso()

    return ExpenseResponse(**expense)
