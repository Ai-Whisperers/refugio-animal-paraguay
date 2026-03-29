"""Pydantic schemas for GDPR data deletion requests and responses."""

from uuid import UUID

from pydantic import BaseModel


class GDPRDeletionRequest(BaseModel):
    """Request to delete/anonymize personal data under GDPR Article 17."""

    user_id: UUID
    donor_id: UUID | None = None
    adopter_id: UUID | None = None


class GDPRDeletionResponse(BaseModel):
    """Summary of GDPR deletion actions taken."""

    user_id: str
    user_deactivated: bool
    consents_deleted: int
    notifications_deleted: int
    donor_anonymized: bool
    adopter_anonymized: bool
    # Third-party cascade results (Stripe, email lists)
    stripe_subscriptions_cancelled: int
    stripe_subscriptions_failed: int
    stripe_customer_deleted: bool
    email_lists_removed: int
