"""Legal document endpoints (RAP-233, RAP-234, RAP-247).

Provides public access to legal document templates:
  GET /legal/dpa                      — Data Processing Agreement template
  GET /legal/sub-processors           — Sub-processor registry
  GET /legal/record-retention-policy  — Paraguayan record retention policy
"""

from datetime import date

from fastapi import APIRouter

from src.services.paraguayan_retention_service import RETENTION_POLICY

router = APIRouter(prefix="/legal", tags=["legal"])

# DPA template last reviewed date
DPA_LAST_UPDATED = date(2026, 3, 29).isoformat()

# The Controller is the shelter; the Processor would be any third-party
# service provider signed up by a donor or partner. This template covers
# the relationship when the shelter acts as a Data Controller engaging
# a third-party Data Processor (e.g. a partner clinic, volunteer org).


@router.get("/dpa", summary="Data Processing Agreement template")
async def get_dpa_template() -> dict:
    """Return the DPA template used between the shelter (Controller) and third-party processors.

    This template is provided for reference. Parties must sign a specific
    agreement before processing begins. Contact privacidad@refugioanimal.com.py.
    """
    return {
        "document": "Data Processing Agreement",
        "version": "1.0",
        "last_updated": DPA_LAST_UPDATED,
        "controller": {
            "name": "Refugio Animal Paraguay",
            "address": "Asuncion, Paraguay",
            "contact": "privacidad@refugioanimal.com.py",
        },
        "sections": [
            {
                "id": "1",
                "title": "Subject matter and duration",
                "body": (
                    "This Data Processing Agreement (DPA) governs the processing of personal data "
                    "by the Processor on behalf of the Controller as described in the main service agreement. "
                    "The DPA is effective for the duration of the service agreement and terminates automatically "
                    "upon its expiry or termination."
                ),
            },
            {
                "id": "2",
                "title": "Nature and purpose of processing",
                "body": (
                    "The Processor may only process personal data for the specific purposes defined in the "
                    "service agreement (e.g. veterinary care, volunteer coordination, donation processing). "
                    "Processing for any other purpose requires prior written consent from the Controller."
                ),
            },
            {
                "id": "3",
                "title": "Categories of data subjects and personal data",
                "body": (
                    "Data subjects may include: donors, adopters, volunteers, rescuers, and shelter staff. "
                    "Personal data categories processed may include: name, email address, phone number, "
                    "address, financial transaction data (amounts, payment references), and where applicable, "
                    "health data for animals under veterinary care."
                ),
            },
            {
                "id": "4",
                "title": "Processor obligations",
                "body": (
                    "The Processor shall: (a) process personal data only on documented instructions from the "
                    "Controller; (b) ensure that authorized persons are bound by confidentiality; "
                    "(c) implement appropriate technical and organizational security measures (Article 32 GDPR); "
                    "(d) assist the Controller in fulfilling data subject rights requests; "
                    "(e) delete or return all personal data upon termination; "
                    "(f) make available all information necessary to demonstrate compliance."
                ),
            },
            {
                "id": "5",
                "title": "Sub-processors",
                "body": (
                    "The Processor shall not engage sub-processors without prior written authorization from the "
                    "Controller. The Controller may consult the shelter's sub-processor registry at "
                    "/legal/sub-processors. The Processor must impose the same data protection obligations on "
                    "any approved sub-processors."
                ),
            },
            {
                "id": "6",
                "title": "Security measures",
                "body": (
                    "The Processor shall implement measures including but not limited to: "
                    "encryption of personal data in transit and at rest; "
                    "access controls and authentication; "
                    "regular security testing and review; "
                    "procedures for regularly testing, assessing, and evaluating effectiveness of security."
                ),
            },
            {
                "id": "7",
                "title": "Data breach notification",
                "body": (
                    "The Processor shall notify the Controller without undue delay (within 24 hours) "
                    "after becoming aware of a personal data breach. Notification shall include: "
                    "nature of the breach, categories and approximate number of data subjects concerned, "
                    "likely consequences, and measures taken or proposed."
                ),
            },
            {
                "id": "8",
                "title": "Data transfers",
                "body": (
                    "Personal data may only be transferred to third countries outside the EEA if an "
                    "adequate level of protection is ensured (e.g. EU adequacy decision, Standard Contractual "
                    "Clauses, or binding corporate rules). The Processor must notify the Controller of any "
                    "intended cross-border transfers."
                ),
            },
            {
                "id": "9",
                "title": "Governing law",
                "body": (
                    "This DPA is governed by the laws of the Republic of Paraguay and, where the Controller's "
                    "data subjects are located in the European Union, also by Regulation (EU) 2016/679 (GDPR). "
                    "Disputes shall be submitted to the competent courts in Asuncion, Paraguay."
                ),
            },
        ],
        "signature_fields": [
            {
                "party": "Controller",
                "name": "Refugio Animal Paraguay",
                "title": "Data Controller representative",
                "date": None,
                "signature": None,
            },
            {
                "party": "Processor",
                "name": None,
                "title": "Data Processor representative",
                "date": None,
                "signature": None,
            },
        ],
        "contact_for_execution": "privacidad@refugioanimal.com.py",
    }


# ---------------------------------------------------------------------------
# Paraguayan record retention policy (RAP-247)
# ---------------------------------------------------------------------------

RETENTION_POLICY_LAST_UPDATED = date(2026, 3, 29).isoformat()


@router.get("/record-retention-policy", summary="Paraguayan record retention policy")
async def get_record_retention_policy() -> dict:
    """Return the mandatory record retention periods per Paraguayan law.

    Covers:
    - Adoption contracts (Codigo Civil Art. 633): 10 years
    - Animal health records (Ley 4840/2013): 5 years
    - Vaccination records (Ley 3140/2006): 5 years
    - Donation/financial records (Ley 125/91): 5 years
    - Adopter personal data: 5 years
    - General correspondence: 2 years

    These are minimum retention periods. The shelter may retain records longer.
    """
    return {
        "document": "Paraguayan Record Retention Policy",
        "version": "1.0",
        "last_updated": RETENTION_POLICY_LAST_UPDATED,
        "jurisdiction": "Republic of Paraguay",
        "note": (
            "These are minimum mandatory retention periods under Paraguayan law. "
            "The shelter may retain records for longer periods at its discretion."
        ),
        "policies": RETENTION_POLICY,
    }
