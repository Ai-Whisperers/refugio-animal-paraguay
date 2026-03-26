"""SEPA Direct Debit router.

Endpoints for managing SEPA mandates for recurring EU donations.

Endpoints:
  POST /donations/sepa-setup            -- create SEPA mandate + SetupIntent
  GET  /donors/{donor_id}/mandates      -- list donor's SEPA mandates
  DELETE /donors/{donor_id}/mandates/{mandate_id} -- revoke a mandate
"""

import logging
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.donation import Donor
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.sepa import (
    SepaMandateListResponse,
    SepaMandateResponse,
    SepaSetupRequest,
    SepaSetupResponse,
)
from src.services.sepa_service import (
    create_sepa_setup,
    get_donor_mandates,
    revoke_mandate,
)
from src.utils.iban import validate_iban

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sepa"])


def _get_stripe_key() -> str:
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway not configured",
        )
    return key


@router.post(
    "/donations/sepa-setup",
    response_model=SepaSetupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def setup_sepa_mandate(
    payload: SepaSetupRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SepaSetupResponse:
    """Create a SEPA Direct Debit mandate and Stripe SetupIntent.

    Staff creates the mandate on behalf of a donor. Returns a client_secret
    for the frontend to confirm the mandate via Stripe.js.
    """
    # Validate IBAN format
    if not validate_iban(payload.iban):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid IBAN format",
        )

    stripe_key = _get_stripe_key()

    try:
        mandate, client_secret = await create_sepa_setup(
            db=db,
            donor_id=payload.donor_id,
            iban=payload.iban,
            amount_cents=payload.amount_cents,
            interval=payload.interval,
            stripe_api_key=stripe_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return SepaSetupResponse(
        mandate_id=mandate.id,
        donor_id=mandate.donor_id,
        stripe_setup_intent_id=mandate.stripe_setup_intent_id or "",
        client_secret=client_secret,
        amount_cents=mandate.amount_cents,
        interval=mandate.interval,
    )


@router.get(
    "/donors/{donor_id}/mandates",
    response_model=SepaMandateListResponse,
)
async def list_donor_mandates(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SepaMandateListResponse:
    """List all SEPA mandates for a donor."""
    # Verify donor exists
    donor = await db.get(Donor, donor_id)
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )

    mandates = await get_donor_mandates(db, donor_id)
    return SepaMandateListResponse(
        donor_id=donor_id,
        mandates=[SepaMandateResponse.model_validate(m) for m in mandates],
    )


@router.delete(
    "/donors/{donor_id}/mandates/{mandate_id}",
    response_model=SepaMandateResponse,
)
async def revoke_donor_mandate(
    donor_id: UUID,
    mandate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_staff),
) -> SepaMandateResponse:
    """Revoke a SEPA mandate. Cancels the Stripe subscription if active."""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")

    mandate = await revoke_mandate(
        db=db,
        mandate_id=mandate_id,
        stripe_api_key=stripe_key or None,
    )

    if mandate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandate not found",
        )

    if mandate.donor_id != donor_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandate not found for this donor",
        )

    return SepaMandateResponse.model_validate(mandate)
