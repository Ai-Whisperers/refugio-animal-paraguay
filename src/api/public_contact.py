"""Public contact and animal inquiry endpoints.

Allows unauthenticated visitors to submit contact forms and
animal-specific inquiries. Rate limited to prevent abuse.

Endpoints:
  POST /public/contact                       -- general contact form
  POST /public/animals/{animal_id}/inquiries -- animal-specific inquiry
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.animal import Animal
from src.db.models.contact_submission import ContactFormType, ContactSubmission
from src.db.session import get_db
from src.middleware.rate_limiter import limiter
from src.schemas.contact import (
    AnimalInquiryCreate,
    ContactFormCreate,
    ContactSubmissionResponse,
)

PUBLIC_CONTACT_RATE_LIMIT = "10/hour"

router = APIRouter(prefix="/public", tags=["public"])


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Use leftmost IP (actual client)
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post(
    "/contact",
    response_model=ContactSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a general contact form",
)
@limiter.limit(PUBLIC_CONTACT_RATE_LIMIT)
async def submit_contact_form(
    request: Request,
    payload: ContactFormCreate,
    db: AsyncSession = Depends(get_db),
) -> ContactSubmissionResponse:
    """Accept a general contact form submission from a public visitor."""
    submission = ContactSubmission(
        form_type=ContactFormType.GENERAL.value,
        visitor_name=payload.visitor_name,
        visitor_email=str(payload.visitor_email),
        subject=payload.subject,
        message=payload.message,
        ip_address=_get_client_ip(request),
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    return ContactSubmissionResponse(
        id=submission.id,
        form_type=submission.form_type,
        submitted_at=submission.created_at,
    )


@router.post(
    "/animals/{animal_id}/inquiries",
    response_model=ContactSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an inquiry about a specific animal",
)
@limiter.limit(PUBLIC_CONTACT_RATE_LIMIT)
async def submit_animal_inquiry(
    request: Request,
    animal_id: UUID,
    payload: AnimalInquiryCreate,
    db: AsyncSession = Depends(get_db),
) -> ContactSubmissionResponse:
    """Accept an animal-specific inquiry from a public visitor."""
    # Verify animal exists
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Animal not found",
        )

    submission = ContactSubmission(
        form_type=ContactFormType.ANIMAL_INQUIRY.value,
        visitor_name=payload.visitor_name,
        visitor_email=str(payload.visitor_email),
        message=payload.message,
        animal_id=animal_id,
        ip_address=_get_client_ip(request),
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    return ContactSubmissionResponse(
        id=submission.id,
        form_type=submission.form_type,
        submitted_at=submission.created_at,
    )
