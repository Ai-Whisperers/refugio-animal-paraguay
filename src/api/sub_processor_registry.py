"""Sub-processor registry endpoint (RAP-234).

GDPR Article 28(3)(d) requires data controllers to document and disclose
sub-processors. This endpoint provides a public registry of all third-party
processors used by Refugio Animal Paraguay.

Endpoints:
  GET /legal/sub-processors  — public sub-processor registry
"""

from datetime import date

from fastapi import APIRouter

router = APIRouter(prefix="/legal", tags=["legal"])

REGISTRY_LAST_UPDATED = date(2026, 3, 29).isoformat()

# Sub-processors are third-party services that may process personal data
# on behalf of the Controller (Refugio Animal Paraguay).
SUB_PROCESSORS: list[dict] = [
    {
        "name": "Stripe, Inc.",
        "role": "Payment processor",
        "data_processed": [
            "Donor name",
            "Email address",
            "Payment card details (tokenised)",
            "Billing address",
            "Transaction amounts and references",
        ],
        "purpose": "Processing online donations, SEPA mandates, subscriptions, and issuing payment confirmations",
        "data_location": "United States (with SCCs / EU adequacy mechanisms)",
        "privacy_policy": "https://stripe.com/privacy",
        "dpa_available": True,
    },
    {
        "name": "Twilio, Inc.",
        "role": "WhatsApp / SMS notification provider",
        "data_processed": [
            "Recipient phone number",
            "Notification content (name, adoption/donation status)",
        ],
        "purpose": "Sending WhatsApp and SMS notifications for adoption status updates, donation receipts, and campaign alerts",
        "data_location": "United States (with SCCs)",
        "privacy_policy": "https://www.twilio.com/en-us/legal/privacy",
        "dpa_available": True,
    },
    {
        "name": "SMTP email provider (aiosmtplib / configured SMTP)",
        "role": "Transactional email delivery",
        "data_processed": [
            "Recipient email address",
            "Recipient name",
            "Email content (adoption confirmations, receipts, follow-ups)",
        ],
        "purpose": "Sending transactional emails for adoption confirmations, donation receipts, password resets, and system notifications",
        "data_location": "Dependent on configured SMTP provider",
        "privacy_policy": None,
        "dpa_available": False,
        "notes": "Operator must configure SMTP provider and maintain a separate DPA if the provider processes EU personal data.",
    },
    {
        "name": "Sentry (Functional Software, Inc.)",
        "role": "Error monitoring and performance tracking",
        "data_processed": [
            "IP address (truncated where possible)",
            "Browser / device metadata",
            "Error stack traces (may contain incidental personal data)",
        ],
        "purpose": "Detecting and diagnosing application errors and performance issues in production",
        "data_location": "United States (with SCCs)",
        "privacy_policy": "https://sentry.io/privacy/",
        "dpa_available": True,
    },
    {
        "name": "Hostinger (Hostinger International Ltd.)",
        "role": "Cloud hosting and infrastructure provider (VPS)",
        "data_processed": [
            "All data stored in the application database",
            "Server logs (IP addresses, request metadata)",
        ],
        "purpose": "Hosting the application, database, and associated infrastructure at sunstein.cloud/petShelter",
        "data_location": "European Union (Lithuania)",
        "privacy_policy": "https://www.hostinger.com/privacy-policy",
        "dpa_available": True,
    },
    {
        "name": "Amazon Web Services (AWS) / S3-compatible storage",
        "role": "Object storage for uploaded media",
        "data_processed": [
            "Animal photos",
            "Medical documents",
            "Campaign images",
            "User-uploaded files",
        ],
        "purpose": "Storing and serving animal photos, medical records, campaign images, and other uploaded media",
        "data_location": "Configurable (operator must set region; EU recommended for GDPR compliance)",
        "privacy_policy": "https://aws.amazon.com/privacy/",
        "dpa_available": True,
    },
]


@router.get("/sub-processors", summary="Sub-processor registry")
async def get_sub_processor_registry() -> dict:
    """Return the public registry of all third-party sub-processors.

    Published in compliance with GDPR Article 28(3)(d) transparency obligations.
    Contact privacidad@refugioanimal.com.py for DPA copies or questions.
    """
    return {
        "document": "Sub-Processor Registry",
        "controller": "Refugio Animal Paraguay",
        "last_updated": REGISTRY_LAST_UPDATED,
        "contact": "privacidad@refugioanimal.com.py",
        "gdpr_basis": "GDPR Article 28(3)(d) — transparency about sub-processors engaged by the Controller",
        "total_sub_processors": len(SUB_PROCESSORS),
        "sub_processors": SUB_PROCESSORS,
    }
