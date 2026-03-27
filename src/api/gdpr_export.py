"""GDPR data export endpoint.

Endpoints:
  POST /gdpr/data-export — generate GDPR data export (Articles 15 & 20)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_admin
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.error import AUTHENTICATED_RESPONSES
from src.schemas.gdpr_export import GDPRExportRequest, GDPRExportResponse
from src.services.gdpr_export_service import generate_data_export

router = APIRouter(prefix="/gdpr", tags=["gdpr"], responses=AUTHENTICATED_RESPONSES)


@router.post("/data-export", response_model=GDPRExportResponse)
async def export_personal_data(
    payload: GDPRExportRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """Generate a GDPR data export for a user.

    Admin-only endpoint. Returns all personal data associated with the
    specified user in a structured, machine-readable JSON format compliant
    with GDPR Articles 15 (Right of Access) and 20 (Data Portability).
    """
    return await generate_data_export(
        db,
        user_id=payload.user_id,
        donor_id=payload.donor_id,
        adopter_id=payload.adopter_id,
    )
