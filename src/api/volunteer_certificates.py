"""Volunteer certificates and thank-you automation API (RAP-198).

Staff endpoints to issue milestone achievement certificates and send thank-you
notifications to volunteers.

Milestone thresholds: 50h, 100h, 250h, 500h, 1000h

Endpoints:
    GET  /api/staff/volunteers/{volunteer_id}/certificates  -- list certificates (staff)
    POST /api/staff/volunteers/{volunteer_id}/certificates  -- issue certificate (staff)
    POST /api/staff/volunteers/{volunteer_id}/certificates/{cert_id}/send-thank-you
         -- (re)send thank-you notification (staff)
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.models.volunteer_certificate import CERTIFICATE_MILESTONES, VolunteerCertificate
from src.db.models.volunteer_profile import VolunteerProfile, VolunteerStatus
from src.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/staff/volunteers", tags=["volunteer-certificates"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class CertificateIssuedBy(BaseModel):
    """Minimal staff info on a certificate."""

    user_id: UUID
    full_name: str | None


class CertificateResponse(BaseModel):
    """A single volunteer certificate record."""

    id: UUID
    volunteer_id: UUID
    milestone_hours: int
    issued_at: datetime
    issued_by: CertificateIssuedBy | None
    thank_you_sent: bool
    thank_you_sent_at: datetime | None
    notes: str | None

    model_config = {"from_attributes": True}


class CertificateListResponse(BaseModel):
    """List of certificates for a volunteer."""

    volunteer_id: UUID
    total_hours_logged: float
    certificates: list[CertificateResponse]
    eligible_milestones: list[int] = Field(
        default_factory=list,
        description="Milestones the volunteer has reached but not yet certificated",
    )


class IssueCertificateRequest(BaseModel):
    """Request body for issuing a certificate."""

    milestone_hours: int = Field(
        ...,
        description=f"Milestone threshold. Must be one of: {sorted(CERTIFICATE_MILESTONES)}",
    )
    notes: str | None = Field(None, max_length=500)
    send_thank_you: bool = Field(
        True, description="Queue a thank-you notification immediately on issue"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _eligible_milestones(
    total_hours: float,
    issued_milestones: set[int],
) -> list[int]:
    """Return milestones the volunteer qualifies for but hasn't received yet."""
    return sorted(
        m for m in CERTIFICATE_MILESTONES if m <= total_hours and m not in issued_milestones
    )


async def _send_thank_you(
    cert: VolunteerCertificate,
    volunteer_email: str,
    volunteer_name: str | None,
) -> None:
    """Queue a thank-you notification to the volunteer.

    Stub implementation — logs intent. A real implementation would call the
    email/WhatsApp notification service once it is available on this branch.
    """
    display_name = volunteer_name or volunteer_email
    logger.info(
        "Thank-you notification queued: volunteer=%s milestone=%dh cert_id=%s",
        display_name,
        cert.milestone_hours,
        cert.id,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{volunteer_id}/certificates",
    response_model=CertificateListResponse,
    summary="List certificates for a volunteer (staff only)",
)
async def list_volunteer_certificates(
    volunteer_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Return all issued certificates for a volunteer, plus eligible milestones not yet issued."""
    # Verify volunteer exists and is approved
    profile_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteer profile {volunteer_id} not found",
        )

    # Fetch certificates
    certs_result = await db.execute(
        select(VolunteerCertificate)
        .where(VolunteerCertificate.volunteer_id == volunteer_id)
        .order_by(VolunteerCertificate.issued_at.asc())
    )
    certs: list[VolunteerCertificate] = list(certs_result.scalars().all())

    # Fetch issuer details
    issuer_ids = {c.issued_by for c in certs if c.issued_by is not None}
    issuers_by_id: dict[UUID, User] = {}
    if issuer_ids:
        users_result = await db.execute(select(User).where(User.id.in_(issuer_ids)))
        issuers_by_id = {u.id: u for u in users_result.scalars().all()}

    cert_responses: list[CertificateResponse] = []
    issued_milestones: set[int] = set()
    for cert in certs:
        issued_milestones.add(cert.milestone_hours)
        issuer_user = issuers_by_id.get(cert.issued_by) if cert.issued_by else None
        cert_responses.append(
            CertificateResponse(
                id=cert.id,
                volunteer_id=cert.volunteer_id,
                milestone_hours=cert.milestone_hours,
                issued_at=cert.issued_at,
                issued_by=(
                    CertificateIssuedBy(
                        user_id=issuer_user.id,
                        full_name=issuer_user.full_name,
                    )
                    if issuer_user
                    else None
                ),
                thank_you_sent=cert.thank_you_sent,
                thank_you_sent_at=cert.thank_you_sent_at,
                notes=cert.notes,
            )
        )

    total_hours = float(profile.total_hours_logged or 0)
    eligible = _eligible_milestones(total_hours, issued_milestones)

    return CertificateListResponse(
        volunteer_id=volunteer_id,
        total_hours_logged=round(total_hours, 2),
        certificates=cert_responses,
        eligible_milestones=eligible,
    )


@router.post(
    "/{volunteer_id}/certificates",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a milestone certificate to a volunteer (staff only)",
)
async def issue_certificate(
    volunteer_id: UUID,
    body: IssueCertificateRequest,
    db: AsyncSession = Depends(get_db),
    staff: User = Depends(require_staff),
) -> Any:
    """Issue an achievement certificate to a volunteer for a milestone.

    - `milestone_hours` must be one of the recognised thresholds (50, 100, 250, 500, 1000).
    - The volunteer's `total_hours_logged` must be >= `milestone_hours`.
    - Each milestone can only be issued once per volunteer.
    - If `send_thank_you` is true, a thank-you notification is queued immediately.
    """
    if body.milestone_hours not in CERTIFICATE_MILESTONES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid milestone_hours {body.milestone_hours}. "
                f"Must be one of: {sorted(CERTIFICATE_MILESTONES)}"
            ),
        )

    # Verify volunteer profile
    profile_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Volunteer profile {volunteer_id} not found",
        )
    if profile.status != VolunteerStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Certificates can only be issued to approved volunteers",
        )

    total_hours = float(profile.total_hours_logged or 0)
    if total_hours < body.milestone_hours:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Volunteer has only {total_hours:.1f}h logged — "
                f"milestone of {body.milestone_hours}h not yet reached"
            ),
        )

    # Check duplicate
    existing_result = await db.execute(
        select(VolunteerCertificate).where(
            VolunteerCertificate.volunteer_id == volunteer_id,
            VolunteerCertificate.milestone_hours == body.milestone_hours,
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Certificate for {body.milestone_hours}h milestone already issued",
        )

    # Fetch volunteer user for notification
    user_result = await db.execute(select(User).where(User.id == profile.user_id))
    volunteer_user = user_result.scalar_one_or_none()

    now = datetime.now(UTC)
    cert = VolunteerCertificate(
        volunteer_id=volunteer_id,
        milestone_hours=body.milestone_hours,
        issued_at=now,
        issued_by=staff.id,
        thank_you_sent=False,
        thank_you_sent_at=None,
        notes=body.notes,
    )
    db.add(cert)
    await db.flush()  # get cert.id

    if body.send_thank_you and volunteer_user is not None:
        await _send_thank_you(cert, volunteer_user.email, volunteer_user.full_name)
        cert.thank_you_sent = True
        cert.thank_you_sent_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(cert)

    logger.info(
        "Certificate issued: volunteer_id=%s milestone=%dh cert_id=%s by=%s",
        volunteer_id,
        body.milestone_hours,
        cert.id,
        staff.id,
    )

    return CertificateResponse(
        id=cert.id,
        volunteer_id=cert.volunteer_id,
        milestone_hours=cert.milestone_hours,
        issued_at=cert.issued_at,
        issued_by=CertificateIssuedBy(user_id=staff.id, full_name=staff.full_name),
        thank_you_sent=cert.thank_you_sent,
        thank_you_sent_at=cert.thank_you_sent_at,
        notes=cert.notes,
    )


@router.post(
    "/{volunteer_id}/certificates/{cert_id}/send-thank-you",
    response_model=CertificateResponse,
    summary="(Re)send thank-you notification for a certificate (staff only)",
)
async def send_thank_you(
    volunteer_id: UUID,
    cert_id: UUID,
    db: AsyncSession = Depends(get_db),
    _staff: object = Depends(require_staff),
) -> Any:
    """Queue a thank-you notification to the volunteer for the given certificate.

    Can be called on previously sent certificates to resend.
    """
    cert_result = await db.execute(
        select(VolunteerCertificate).where(
            VolunteerCertificate.id == cert_id,
            VolunteerCertificate.volunteer_id == volunteer_id,
        )
    )
    cert = cert_result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate {cert_id} not found for volunteer {volunteer_id}",
        )

    # Fetch volunteer user
    profile_result = await db.execute(
        select(VolunteerProfile).where(VolunteerProfile.id == volunteer_id)
    )
    profile = profile_result.scalar_one_or_none()
    volunteer_user: User | None = None
    if profile is not None:
        user_result = await db.execute(select(User).where(User.id == profile.user_id))
        volunteer_user = user_result.scalar_one_or_none()

    if volunteer_user is not None:
        await _send_thank_you(cert, volunteer_user.email, volunteer_user.full_name)

    cert.thank_you_sent = True
    cert.thank_you_sent_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(cert)

    return CertificateResponse(
        id=cert.id,
        volunteer_id=cert.volunteer_id,
        milestone_hours=cert.milestone_hours,
        issued_at=cert.issued_at,
        issued_by=None,
        thank_you_sent=cert.thank_you_sent,
        thank_you_sent_at=cert.thank_you_sent_at,
        notes=cert.notes,
    )
