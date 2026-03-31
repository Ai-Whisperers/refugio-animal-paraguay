"""GDPR data deletion endpoints.

Endpoints:
  POST /gdpr/deletion-request — process GDPR right to erasure request (Article 17)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.gdpr_deletion import GDPRDeletionRequest, GDPRDeletionResponse
from src.services.gdpr_deletion_service import process_deletion_request

router = APIRouter(prefix="/gdpr", tags=["gdpr"], responses=AUTHENTICATED_RESPONSES)


@router.post("/deletion-request", response_model=GDPRDeletionResponse)
async def request_data_deletion(
    payload: GDPRDeletionRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """Process a GDPR Article 17 data deletion request.

    Admin-only endpoint. Anonymizes personal data across all relevant tables
    while preserving non-personal records for operational integrity.

    Covered entities:
    - User account (email, full_name, phone)
    - Donor profile (full_name, email, country)
    - Adopter profile (full_name, email, phone, address)
    - Volunteer profile (emergency contact, bio, motivation)
    - Rescuer profile (display_name, slug, bio, location, social links, WhatsApp)
    - Foster profile (motivation, experience description)
    - Consent records (hard deleted)
    - Notification records (hard deleted)

    This action is irreversible.
    """
    return await process_deletion_request(
        db,
        user_id=payload.user_id,
        donor_id=payload.donor_id,
        adopter_id=payload.adopter_id,
        volunteer_id=payload.volunteer_id,
        rescuer_id=payload.rescuer_id,
        foster_id=payload.foster_id,
    )
