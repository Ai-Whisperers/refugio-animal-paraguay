"""Adoption Requests workflow router.

Endpoints:
  GET    /adoption-requests              — paginated list (filter by status / animal / adopter)
  GET    /adoption-requests/{id}         — single request or 404
  POST   /adoption-requests              — create, returns 201
  PATCH  /adoption-requests/{id}/status  — transition status; approved sets animal → adopted
  POST   /adoption-requests/{id}/contract — generate adoption contract PDF
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.models.user import User
from src.db.session import get_db
from src.events.bus import EventBus
from src.events.dependencies import get_event_bus
from src.events.domain_events import (
    create_adoption_request_created,
    create_adoption_status_changed,
)
from src.schemas.adoption_request import (
    AdoptionRequestCreate,
    AdoptionRequestResponse,
    AdoptionRequestStatusUpdate,
    ContractGeneratedResponse,
)
from src.schemas.error import RESOURCE_RESPONSES
from src.services.contract_service import ContractData, ContractPDFGenerator

router = APIRouter(prefix="/adoption-requests", tags=["adoption-requests"], responses=RESOURCE_RESPONSES)

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100

# ---------------------------------------------------------------------------
# Valid status transitions
# ---------------------------------------------------------------------------
_ALLOWED_TRANSITIONS: dict[AdoptionRequestStatus, set[AdoptionRequestStatus]] = {
    AdoptionRequestStatus.PENDING: {
        AdoptionRequestStatus.APPROVED,
        AdoptionRequestStatus.REJECTED,
        AdoptionRequestStatus.CANCELLED,
    },
    AdoptionRequestStatus.APPROVED: {AdoptionRequestStatus.CANCELLED},
    AdoptionRequestStatus.REJECTED: {AdoptionRequestStatus.CANCELLED},
    AdoptionRequestStatus.CANCELLED: set(),
}


@router.get("", response_model=list[AdoptionRequestResponse])
async def list_adoption_requests(
    status_filter: AdoptionRequestStatus | None = Query(default=None, alias="status"),
    animal_id: UUID | None = Query(default=None),
    adopter_id: UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
) -> list[AdoptionRequest]:
    stmt = (
        select(AdoptionRequest)
        .offset(offset)
        .limit(limit)
        .order_by(AdoptionRequest.submitted_at.desc())
    )
    if status_filter is not None:
        stmt = stmt.where(AdoptionRequest.status == status_filter.value)
    if animal_id is not None:
        stmt = stmt.where(AdoptionRequest.animal_id == animal_id)
    if adopter_id is not None:
        stmt = stmt.where(AdoptionRequest.adopter_id == adopter_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{request_id}", response_model=AdoptionRequestResponse)
async def get_adoption_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> AdoptionRequest:
    req = await db.get(AdoptionRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adoption request not found",
        )
    return req


@router.post("", response_model=AdoptionRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_adoption_request(
    payload: AdoptionRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
    event_bus: EventBus = Depends(get_event_bus),
) -> AdoptionRequest:
    # Validate animal exists
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )

    # Validate adopter exists and is not soft-deleted
    adopter = await db.get(Adopter, payload.adopter_id)
    if adopter is None or adopter.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adopter not found",
        )

    req = AdoptionRequest(
        animal_id=payload.animal_id,
        adopter_id=payload.adopter_id,
        status=AdoptionRequestStatus.PENDING.value,
        submitted_at=datetime.now(UTC),
        notes=payload.notes,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)

    # Publish domain event for notification handlers
    if event_bus.is_running:
        event = create_adoption_request_created(
            aggregate_id=req.id,
            adopter_name=adopter.full_name,
            animal_name=animal.name,
            adopter_email=adopter.email,
            actor_id=current_user.id,
        )
        await event_bus.publish(event)

    return req


@router.patch("/{request_id}/status", response_model=AdoptionRequestResponse)
async def update_adoption_request_status(
    request_id: UUID,
    payload: AdoptionRequestStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
    event_bus: EventBus = Depends(get_event_bus),
) -> AdoptionRequest:
    req = await db.get(AdoptionRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adoption request not found",
        )

    current = AdoptionRequestStatus(req.status)
    new_status = payload.status

    if new_status not in _ALLOWED_TRANSITIONS[current]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Cannot transition adoption request from '{current.value}'"
                f" to '{new_status.value}'"
            ),
        )

    old_status_value = current.value
    req.status = new_status.value
    req.decided_at = datetime.now(UTC)
    req.updated_at = datetime.now(UTC)

    # Store decision notes if provided
    if payload.notes is not None:
        req.notes = payload.notes

    # Side-effect: approved request marks animal as adopted
    if new_status == AdoptionRequestStatus.APPROVED:
        animal = await db.get(Animal, req.animal_id)
        if animal is not None:
            animal.status = "adopted"
            animal.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(req)

    # Publish domain event for notification handlers
    if event_bus.is_running:
        event = create_adoption_status_changed(
            aggregate_id=req.id,
            old_status=old_status_value,
            new_status=new_status.value,
            actor_id=current_user.id,
            notes=payload.notes,
        )
        await event_bus.publish(event)

    return req


@router.post(
    "/{request_id}/contract",
    response_model=ContractGeneratedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_adoption_contract(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> dict:
    """Generate a PDF adoption contract for an approved request.

    Only requests with status 'approved' can have contracts generated.
    Re-generating overwrites the previous PDF.
    """
    req = await db.get(AdoptionRequest, request_id)
    if req is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adoption request not found",
        )

    if req.status != AdoptionRequestStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Contract can only be generated for approved adoption requests",
        )

    # Load related adopter and animal
    adopter = await db.get(Adopter, req.adopter_id)
    if adopter is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adopter not found for this request",
        )

    animal = await db.get(Animal, req.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found for this request",
        )

    contract_data = ContractData(
        request_id=req.id,
        adopter_name=adopter.full_name,
        adopter_email=adopter.email,
        adopter_phone=adopter.phone,
        adopter_address=adopter.address,
        animal_name=animal.name,
        animal_species=animal.species,
        animal_breed=animal.breed,
        approved_at=req.decided_at,
    )

    generator = ContractPDFGenerator()
    pdf_path = generator.generate(contract_data)

    now = datetime.now(UTC)
    req.contract_pdf_path = str(pdf_path)
    req.contract_generated_at = now
    req.updated_at = now

    await db.flush()
    await db.refresh(req)

    return {
        "request_id": req.id,
        "contract_pdf_path": req.contract_pdf_path,
        "contract_generated_at": req.contract_generated_at,
    }
