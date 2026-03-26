"""Consent management router.

GDPR Article 7 compliant consent tracking endpoints.

Endpoints:
  GET  /users/{user_id}/consents         -- get current consent summary
  GET  /users/{user_id}/consents/details  -- get full consent records
  PUT  /users/{user_id}/consents         -- update consent preferences
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.user import User
from src.db.models.user_consent import ConsentType
from src.db.session import get_db
from src.schemas.consent import (
    ConsentBulkUpdate,
    ConsentResponse,
    ConsentSummary,
)
from src.services.consent_service import (
    get_consent_summary,
    get_user_consents,
    grant_consent,
    revoke_consent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["consents"])


@router.get("/{user_id}/consents", response_model=ConsentSummary)
async def get_consents(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> ConsentSummary:
    """Get consent summary for a user — shows all types with active/inactive status."""
    summary = await get_consent_summary(db, user_id)
    return ConsentSummary(
        user_id=user_id,
        consents={ConsentType(k): v for k, v in summary.items()},
    )


@router.get(
    "/{user_id}/consents/details",
    response_model=list[ConsentResponse],
)
async def get_consent_details(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> list:
    """Get full consent records for a user including dates, method, and metadata."""
    return await get_user_consents(db, user_id)


@router.put("/{user_id}/consents", response_model=list[ConsentResponse])
async def update_consents(
    user_id: UUID,
    payload: ConsentBulkUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_staff),
) -> list:
    """Update consent preferences for a user.

    Accepts a list of consent type + granted pairs. Each consent is either
    granted (True) or revoked (False). Idempotent — re-granting active consent
    is a no-op.
    """
    # Verify target user exists
    target_user = await db.get(User, user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Extract request context for GDPR compliance
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    results = []
    for update in payload.consents:
        if update.granted:
            consent = await grant_consent(
                db=db,
                user_id=user_id,
                consent_type=update.consent_type,
                method=update.method,
                ip_address=ip_address,
                user_agent=user_agent,
                granted_by_staff_id=current_user.id,
                notes=update.notes,
            )
            results.append(consent)
        else:
            consent = await revoke_consent(
                db=db,
                user_id=user_id,
                consent_type=update.consent_type,
                method=update.method,
                ip_address=ip_address,
                user_agent=user_agent,
                notes=update.notes,
            )
            if consent is not None:
                results.append(consent)

    return results
