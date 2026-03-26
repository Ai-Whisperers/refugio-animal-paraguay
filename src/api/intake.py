"""Animal Intake Workflow router.

Endpoints:
  POST   /animals/intake               - process new animal intake (staff only)
  GET    /animals/intake               - list intake records (staff only)
  GET    /animals/intake/{intake_id}   - single intake record (staff only)
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.animal import Animal, AnimalPhoto, AnimalStatus
from src.db.models.intake import IntakeRecord, IntakeSource, handle_quarantine_trigger
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.intake import IntakeCreate, IntakeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/animals/intake", tags=["intake"])

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


@router.post("", response_model=IntakeResponse, status_code=status.HTTP_201_CREATED)
async def create_intake(
    payload: IntakeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> IntakeRecord:
    """Process a new animal intake.

    Creates an Animal record (status=intake, or quarantine if flagged) and
    an IntakeRecord linking the animal to its intake details. Optionally
    attaches photos from provided URLs.
    """
    # Determine initial animal status based on quarantine flag
    animal_status = (
        AnimalStatus.QUARANTINE.value if payload.requires_quarantine else AnimalStatus.INTAKE.value
    )

    # Parse birth_date if provided
    parsed_birth_date: date | None = None
    if payload.birth_date is not None:
        try:
            parsed_birth_date = date.fromisoformat(payload.birth_date)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid birth_date format. Expected YYYY-MM-DD.",
            ) from err

    # Create Animal record
    animal = Animal(
        name=payload.name,
        species=payload.species.value,
        status=animal_status,
        birth_date=parsed_birth_date,
        description=payload.description,
    )
    db.add(animal)
    await db.flush()

    # Attach photos if provided
    for idx, url in enumerate(payload.photo_urls):
        photo = AnimalPhoto(
            animal_id=animal.id,
            url=url,
            caption=f"Intake photo {idx + 1}",
            display_order=idx,
        )
        db.add(photo)

    # Set primary photo URL from first intake photo
    if payload.photo_urls:
        animal.primary_photo_url = payload.photo_urls[0]

    # Create IntakeRecord
    intake = IntakeRecord(
        animal_id=animal.id,
        source=payload.source.value,
        finder_name=payload.finder_name,
        finder_email=payload.finder_email,
        finder_phone=payload.finder_phone,
        location_found=payload.location_found,
        condition_on_arrival=payload.condition_on_arrival,
        requires_quarantine=payload.requires_quarantine,
        staff_id=current_user.id,
        notes=payload.notes,
    )
    db.add(intake)
    await db.flush()

    # Quarantine stub — logs for now, EPIC-4 will create medical records
    handle_quarantine_trigger(intake)

    await db.refresh(intake)
    return intake


@router.get("", response_model=list[IntakeResponse])
async def list_intakes(
    source: IntakeSource | None = Query(default=None, description="Filter by source"),
    requires_quarantine: bool | None = Query(
        default=None, description="Filter by quarantine status"
    ),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> list[IntakeRecord]:
    """List intake records with optional filters. Staff only."""
    stmt = select(IntakeRecord)

    if source is not None:
        stmt = stmt.where(IntakeRecord.source == source.value)
    if requires_quarantine is not None:
        stmt = stmt.where(IntakeRecord.requires_quarantine == requires_quarantine)

    stmt = stmt.offset(offset).limit(limit).order_by(IntakeRecord.intake_date.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{intake_id}", response_model=IntakeResponse)
async def get_intake(
    intake_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> IntakeRecord:
    """Get a single intake record by ID. Staff only."""
    intake = await db.get(IntakeRecord, intake_id)
    if intake is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake record not found",
        )
    return intake
