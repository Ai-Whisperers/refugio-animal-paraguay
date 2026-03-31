"""API endpoints for donor tax ID (BSN/TIN) secure storage.

These endpoints allow staff to store, retrieve, and remove encrypted donor
tax identification numbers. Tax IDs are sensitive personal data and access
is restricted to authenticated staff members.

All storage is encrypted at rest using Fernet symmetric encryption.
Plaintext tax IDs are never logged or included in audit records.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.config import get_settings
from src.db.models.donation import Donor
from src.db.models.user import User
from src.db.session import get_db
from src.services.donor_tax_id_service import (
    VALID_TAX_ID_TYPES,
    DonorTaxIDService,
    TaxIDDecryptionError,
    TaxIDEncryptionKeyNotConfiguredError,
    TaxIDValidationError,
)

router = APIRouter(prefix="/donors", tags=["donor-tax-id"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class DonorTaxIDSetRequest(BaseModel):
    """Request body for setting a donor's tax ID."""

    tax_id: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Plaintext tax ID (BSN, TIN, etc.). Encrypted before storage.",
    )
    tax_id_type: str = Field(
        ...,
        description=f"Tax ID type. Allowed: {sorted(VALID_TAX_ID_TYPES)}",
    )


class DonorTaxIDResponse(BaseModel):
    """Response indicating tax ID status for a donor."""

    donor_id: UUID
    has_tax_id: bool
    tax_id_type: str | None
    # Plaintext only included when explicitly requested by staff
    tax_id: str | None = None


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_tax_id_service() -> DonorTaxIDService:
    """Build a DonorTaxIDService from current settings."""
    settings = get_settings()
    try:
        return DonorTaxIDService(settings.donor_tax_id_encryption_key)
    except TaxIDEncryptionKeyNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Tax ID storage is not configured. "
                "DONOR_TAX_ID_ENCRYPTION_KEY environment variable is not set."
            ),
        ) from exc


async def _get_donor_or_404(donor_id: UUID, db: AsyncSession) -> Donor:
    result = await db.execute(select(Donor).where(Donor.id == donor_id))
    donor = result.scalar_one_or_none()
    if donor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Donor {donor_id} not found.",
        )
    return donor


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.put(
    "/{donor_id}/tax-id",
    response_model=DonorTaxIDResponse,
    status_code=status.HTTP_200_OK,
    summary="Set or update donor tax ID",
    description=(
        "Store an encrypted tax ID (BSN/TIN) for a donor. "
        "The plaintext value is encrypted at rest and never stored in logs. "
        "Overwrites any previously stored tax ID for this donor."
    ),
)
async def set_donor_tax_id(
    donor_id: UUID,
    body: DonorTaxIDSetRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> DonorTaxIDResponse:
    svc = _get_tax_id_service()
    try:
        DonorTaxIDService.validate_tax_id(body.tax_id, body.tax_id_type)
    except TaxIDValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    donor = await _get_donor_or_404(donor_id, db)
    donor.tax_id_encrypted = svc.encrypt(body.tax_id)
    donor.tax_id_type = body.tax_id_type
    await db.commit()
    await db.refresh(donor)

    return DonorTaxIDResponse(
        donor_id=donor.id,
        has_tax_id=True,
        tax_id_type=donor.tax_id_type,
    )


@router.get(
    "/{donor_id}/tax-id",
    response_model=DonorTaxIDResponse,
    summary="Retrieve donor tax ID (staff only)",
    description=(
        "Return the decrypted tax ID for a donor. "
        "Access is restricted to authenticated staff. "
        "Returns has_tax_id=False if no tax ID is stored."
    ),
)
async def get_donor_tax_id(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> DonorTaxIDResponse:
    donor = await _get_donor_or_404(donor_id, db)

    if not donor.tax_id_encrypted:
        return DonorTaxIDResponse(
            donor_id=donor.id,
            has_tax_id=False,
            tax_id_type=None,
        )

    svc = _get_tax_id_service()
    try:
        plaintext = svc.decrypt(donor.tax_id_encrypted)
    except TaxIDDecryptionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tax ID decryption failed. The stored data may be corrupted.",
        ) from exc

    return DonorTaxIDResponse(
        donor_id=donor.id,
        has_tax_id=True,
        tax_id_type=donor.tax_id_type,
        tax_id=plaintext,
    )


@router.delete(
    "/{donor_id}/tax-id",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove donor tax ID",
    description="Delete the stored tax ID for a donor. This action is irreversible.",
)
async def delete_donor_tax_id(
    donor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> None:
    donor = await _get_donor_or_404(donor_id, db)
    donor.tax_id_encrypted = None
    donor.tax_id_type = None
    await db.commit()
