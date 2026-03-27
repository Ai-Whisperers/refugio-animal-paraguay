"""GDPR data deletion endpoint.

Endpoints:
  POST /gdpr/deletion-request — process GDPR right to erasure request
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

    This action is irreversible.
    """
    return await process_deletion_request(
        db,
        user_id=payload.user_id,
        donor_id=payload.donor_id,
        adopter_id=payload.adopter_id,
    )
