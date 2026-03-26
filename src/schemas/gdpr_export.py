"""Pydantic schemas for GDPR data export requests and responses."""

from uuid import UUID

from pydantic import BaseModel


class GDPRExportRequest(BaseModel):
    """Request to export personal data under GDPR Articles 15 & 20."""

    user_id: UUID
    donor_id: UUID | None = None
    adopter_id: UUID | None = None


class ExportMetadata(BaseModel):
    """Metadata about the export itself."""

    user_id: str
    generated_at: str
    format_version: str
    gdpr_articles: list[str]


class UserProfileExport(BaseModel):
    """Exported user account profile."""

    id: str
    email: str
    role: str
    is_active: bool
    created_at: str | None
    updated_at: str | None


class DonorProfileExport(BaseModel):
    """Exported donor profile."""

    id: str
    full_name: str
    email: str
    country: str | None
    currency_preference: str
    gdpr_consent_at: str | None
    created_at: str | None
    updated_at: str | None


class DonationExport(BaseModel):
    """Exported donation record."""

    id: str
    amount_cents: int
    currency: str
    payment_method: str
    status: str
    receipt_number: str | None
    fund_category: str | None
    notes: str | None
    created_at: str | None


class DonorDataExport(BaseModel):
    """Exported donor data including donations."""

    profile: DonorProfileExport
    donations: list[DonationExport]


class AdopterProfileExport(BaseModel):
    """Exported adopter profile."""

    id: str
    full_name: str
    email: str
    phone: str | None
    address: str | None
    gdpr_consent_at: str | None
    created_at: str | None
    updated_at: str | None


class AdoptionRequestExport(BaseModel):
    """Exported adoption request record."""

    id: str
    animal_id: str
    status: str
    notes: str | None
    created_at: str | None
    updated_at: str | None


class AdopterDataExport(BaseModel):
    """Exported adopter data including adoption requests."""

    profile: AdopterProfileExport
    adoption_requests: list[AdoptionRequestExport]


class ConsentExport(BaseModel):
    """Exported consent record."""

    id: str
    consent_type: str
    status: str
    opt_in_date: str | None
    opt_out_date: str | None
    method: str
    created_at: str | None


class NotificationExport(BaseModel):
    """Exported notification record."""

    id: str
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: str | None


class GDPRExportResponse(BaseModel):
    """Full GDPR data export response."""

    export_metadata: ExportMetadata
    user_profile: UserProfileExport | None
    donor_data: DonorDataExport | None
    adopter_data: AdopterDataExport | None
    consents: list[ConsentExport]
    notifications: list[NotificationExport]
