"""Public adoption application endpoint.

Allows unauthenticated visitors to submit adoption applications.
Creates or reuses an adopter record and creates a pending adoption request.

Endpoints:
  POST /public/adoption-applications  -- submit adoption application (no auth)
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.adopter import Adopter
from src.db.models.adoption_request import AdoptionRequest, AdoptionRequestStatus
from src.db.models.animal import Animal
from src.db.session import get_db
from src.middleware.rate_limiter import limiter
from src.schemas.public_adoption import (
    PublicAdoptionApplicationCreate,
    PublicAdoptionApplicationResponse,
)

PUBLIC_ADOPTION_RATE_LIMIT = "10/hour"

router = APIRouter(prefix="/public", tags=["public"])


@router.post(
    "/adoption-applications",
    response_model=PublicAdoptionApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a public adoption application",
)
@limiter.limit(PUBLIC_ADOPTION_RATE_LIMIT)
async def submit_adoption_application(
    request: Request,
    payload: PublicAdoptionApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> PublicAdoptionApplicationResponse:
    """Accept an adoption application from a public visitor.

    - Validates GDPR consent is given
    - Validates the animal exists and is available
    - Creates or finds an adopter by email
    - Creates a pending adoption request
    """
    # GDPR consent is mandatory
    if not payload.gdpr_consent:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="GDPR consent is required to submit an adoption application",
        )

    # Validate animal exists and is available
    animal = await db.get(Animal, payload.animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )
    if animal.status != "available":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="This animal is not currently available for adoption",
        )

    # Find or create adopter by email
    result = await db.execute(
        select(Adopter).where(
            Adopter.email == str(payload.email),
            Adopter.deleted_at.is_(None),
        )
    )
    adopter = result.scalar_one_or_none()

    now = datetime.now(UTC)

    if adopter is None:
        adopter = Adopter(
            full_name=payload.full_name,
            email=str(payload.email),
            phone=payload.phone,
            gdpr_consent_at=now,
        )
        db.add(adopter)
        await db.flush()
        await db.refresh(adopter)

    # Check for duplicate pending application for same animal
    existing_request = await db.execute(
        select(AdoptionRequest).where(
            AdoptionRequest.adopter_id == adopter.id,
            AdoptionRequest.animal_id == payload.animal_id,
            AdoptionRequest.status == AdoptionRequestStatus.PENDING.value,
        )
    )
    if existing_request.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending application for this animal",
        )

    # Create adoption request
    adoption_request = AdoptionRequest(
        animal_id=payload.animal_id,
        adopter_id=adopter.id,
        status=AdoptionRequestStatus.PENDING.value,
        submitted_at=now,
        notes=payload.message,
    )
    db.add(adoption_request)
    await db.flush()
    await db.refresh(adoption_request)

    return PublicAdoptionApplicationResponse(
        id=adoption_request.id,
        animal_id=adoption_request.animal_id,
        status=adoption_request.status,
        submitted_at=adoption_request.submitted_at,
    )
