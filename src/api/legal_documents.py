"""Legal document endpoints (RAP-233, RAP-234, RAP-246, RAP-247, RAP-249).

Provides public access to legal document templates:
  GET /legal/dpa                      — Data Processing Agreement template (?lang=es|en)
  GET /legal/sub-processors           — Sub-processor registry
  GET /legal/adoption-contract        — Paraguayan adoption contract template
  GET /legal/record-retention-policy  — Paraguayan record retention policy (?lang=es|en)
  GET /legal/supported-languages      — Language discovery endpoint
"""

from datetime import date

from fastapi import APIRouter, Query

from src.services.multilingual_legal_service import (
    DPA_SECTIONS_ES,
    MULTILINGUAL_DOCUMENTS,
    RETENTION_POLICY_DOCUMENT_TITLE_ES,
    RETENTION_POLICY_SUMMARY_ES,
    normalise_language,
)
from src.services.paraguayan_retention_service import RETENTION_POLICY

router = APIRouter(prefix="/legal", tags=["legal"])

# DPA template last reviewed date
DPA_LAST_UPDATED = date(2026, 3, 29).isoformat()

# Adoption contract template last reviewed date (Ley 4840/2013 + Ley 3140/2006)
ADOPTION_CONTRACT_LAST_UPDATED = date(2026, 3, 29).isoformat()

# The Controller is the shelter; the Processor would be any third-party
# service provider signed up by a donor or partner. This template covers
# the relationship when the shelter acts as a Data Controller engaging
# a third-party Data Processor (e.g. a partner clinic, volunteer org).

# English DPA sections (extracted for clarity and to avoid duplication)
_DPA_SECTIONS_EN: list[dict] = [
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
]

_DPA_BY_LANG: dict[str, dict] = {
    "en": {
        "document": "Data Processing Agreement",
        "sections": _DPA_SECTIONS_EN,
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
    },
    "es": {
        "document": "Acuerdo de Procesamiento de Datos",
        "sections": DPA_SECTIONS_ES,
        "signature_fields": [
            {
                "party": "Responsable",
                "name": "Refugio Animal Paraguay",
                "title": "Representante del Responsable del Tratamiento",
                "date": None,
                "signature": None,
            },
            {
                "party": "Procesador",
                "name": None,
                "title": "Representante del Encargado del Tratamiento",
                "date": None,
                "signature": None,
            },
        ],
        "contact_for_execution": "privacidad@refugioanimal.com.py",
    },
}


@router.get("/supported-languages", summary="List supported languages for legal documents")
async def get_supported_languages() -> dict:
    """Return all documents that support multiple languages and the codes available.

    Use the returned language codes as the value for the ?lang= query parameter
    on individual document endpoints. Unsupported codes silently fall back to 'es'.
    """
    return {
        "default_language": "es",
        "supported_languages": [
            {"code": "es", "name": "Español"},
            {"code": "en", "name": "English"},
        ],
        "documents": MULTILINGUAL_DOCUMENTS,
    }


@router.get("/dpa", summary="Data Processing Agreement template")
async def get_dpa_template(
    lang: str = Query(
        default="es",
        description="Document language: 'es' (Spanish, default) or 'en' (English). Unsupported codes fall back to 'es'.",
    ),
) -> dict:
    """Return the DPA template used between the shelter (Controller) and third-party processors.

    Available in Spanish (es, default) and English (en). Unsupported language codes fall back to 'es'.
    This template is provided for reference. Parties must sign a specific
    agreement before processing begins. Contact privacidad@refugioanimal.com.py.
    """
    resolved = normalise_language(lang)
    localised = _DPA_BY_LANG[resolved]
    return {
        "document": localised["document"],
        "version": "1.0",
        "language": resolved,
        "last_updated": DPA_LAST_UPDATED,
        "controller": {
            "name": "Refugio Animal Paraguay",
            "address": "Asuncion, Paraguay",
            "contact": "privacidad@refugioanimal.com.py",
        },
        "sections": localised["sections"],
        "signature_fields": localised["signature_fields"],
        "contact_for_execution": localised["contact_for_execution"],
    }


# ---------------------------------------------------------------------------
# Bilingual clause sets for the adoption contract
# ---------------------------------------------------------------------------

_ADOPTION_CONTRACT_ES = {
    "document": "Contrato de Adopcion de Animal",
    "document_en": "Animal Adoption Contract",
    "legal_basis": [
        "Ley 4840/2013 — Bienestar Animal (Animal Welfare Law)",
        "Ley 3140/2006 — Control de Enfermedades Animales (Animal Disease Control)",
        "Decreto 1237 — Registro Veterinario (SENACSA)",
    ],
    "sections": [
        {
            "id": "1",
            "title": "Descripcion del Animal",
            "title_en": "Animal Description",
            "fields": [
                "especie",
                "raza",
                "sexo",
                "edad_aproximada",
                "descripcion_fisica",
                "numero_senacsa",
            ],
            "body": (
                "El animal objeto del presente contrato se describe a continuacion. "
                "El adoptante reconoce haber verificado el estado de salud del animal "
                "antes de la firma de este contrato."
            ),
        },
        {
            "id": "2",
            "title": "Identificacion del Adoptante",
            "title_en": "Adopter Identification",
            "fields": [
                "nombre_completo",
                "cedula_o_pasaporte",
                "domicilio",
                "telefono",
                "correo_electronico",
            ],
            "body": (
                "El adoptante declara ser mayor de edad y poseer plena capacidad legal "
                "para celebrar el presente contrato conforme a la legislacion paraguaya vigente."
            ),
        },
        {
            "id": "3",
            "title": "Historial de Vacunacion",
            "title_en": "Vaccination History",
            "fields": ["vacuna_rabia", "fecha_rabia", "otras_vacunas"],
            "body": (
                "Conforme a la Ley 3140/2006, el animal cuenta con vacuna antirabica vigente. "
                "El adoptante se compromete a mantener al dia el calendario de vacunacion. "
                "La vacunacion antirabica es obligatoria por ley nacional."
            ),
            "legal_ref": "Ley 3140/2006, Art. 5",
        },
        {
            "id": "4",
            "title": "Clausula de Esterilizacion",
            "title_en": "Sterilization Clause",
            "fields": [
                "ya_esterilizado",
                "compromiso_esterilizacion",
                "fecha_limite_esterilizacion",
            ],
            "body": (
                "En caso de que el animal no haya sido esterilizado al momento de la adopcion, "
                "el adoptante se compromete a esterilizarlo dentro del plazo indicado. "
                "El incumplimiento de esta clausula puede dar lugar a la resolucion del contrato."
            ),
        },
        {
            "id": "5",
            "title": "Politica de Devolucion",
            "title_en": "Return Policy",
            "body": (
                "El adoptante se compromete a devolver el animal al Refugio Animal Paraguay "
                "en caso de no poder continuar con la adopcion. Queda estrictamente prohibido "
                "el abandono del animal en la via publica o en cualquier lugar publico o privado, "
                "en cumplimiento de la Ley 4840/2013."
            ),
            "legal_ref": "Ley 4840/2013, Art. 8",
        },
        {
            "id": "6",
            "title": "Clausula de Inspeccion del Hogar",
            "title_en": "Home Inspection Clause",
            "body": (
                "El Refugio Animal Paraguay se reserva el derecho de realizar visitas de seguimiento "
                "al domicilio del adoptante para verificar las condiciones de vida del animal. "
                "El adoptante autoriza dichas visitas coordinadas con 48 horas de anticipacion."
            ),
        },
        {
            "id": "7",
            "title": "Prohibicion de Reventa o Transferencia",
            "title_en": "Prohibition on Resale or Transfer",
            "body": (
                "El adoptante reconoce que el animal es un ser vivo y no un bien comercializable. "
                "Queda expresamente prohibida la venta, cesion o transferencia del animal a terceros "
                "sin autorizacion previa y escrita del Refugio Animal Paraguay."
            ),
        },
        {
            "id": "8",
            "title": "Obligaciones de Bienestar Animal",
            "title_en": "Animal Welfare Obligations",
            "body": (
                "El adoptante se compromete a: (a) proporcionar alimentacion adecuada y agua fresca; "
                "(b) garantizar atencion veterinaria ante enfermedades o lesiones; "
                "(c) no someter al animal a maltrato fisico o psicologico; "
                "(d) respetar todas las disposiciones de la Ley 4840/2013 de Bienestar Animal."
            ),
            "legal_ref": "Ley 4840/2013, Art. 3-7",
        },
        {
            "id": "9",
            "title": "Reconocimiento de Microchip",
            "title_en": "Microchip Acknowledgment",
            "fields": ["numero_microchip"],
            "body": (
                "En caso de que el animal cuente con microchip de identificacion, el adoptante "
                "reconoce el numero registrado y se compromete a no alterar, extraer ni inutilizar "
                "dicho dispositivo. El microchip es la identificacion oficial del animal."
            ),
        },
        {
            "id": "10",
            "title": "Ley Aplicable y Jurisdiccion",
            "title_en": "Governing Law and Jurisdiction",
            "body": (
                "El presente contrato se rige por las leyes de la Republica del Paraguay, "
                "especialmente la Ley 4840/2013 y la Ley 3140/2006. "
                "Cualquier controversia derivada del presente contrato sera sometida a la "
                "jurisdiccion de los tribunales competentes de Asuncion, Paraguay."
            ),
        },
    ],
    "signature_fields": [
        {
            "party": "adoptante",
            "label": "Adoptante",
            "name": None,
            "cedula": None,
            "date": None,
            "signature": None,
        },
        {
            "party": "shelter",
            "label": "Representante del Refugio Animal Paraguay",
            "name": None,
            "cargo": None,
            "date": None,
            "signature": None,
        },
    ],
    "contact": "adopciones@refugioanimal.com.py",
}

_ADOPTION_CONTRACT_EN = {
    "document": "Animal Adoption Contract",
    "document_es": "Contrato de Adopcion de Animal",
    "legal_basis": [
        "Ley 4840/2013 — Animal Welfare Law (Paraguay)",
        "Ley 3140/2006 — Animal Disease Control Law (Paraguay)",
        "Decreto 1237 — Veterinary Registry (SENACSA)",
    ],
    "sections": [
        {
            "id": "1",
            "title": "Animal Description",
            "title_es": "Descripcion del Animal",
            "fields": [
                "species",
                "breed",
                "sex",
                "approximate_age",
                "physical_description",
                "senacsa_number",
            ],
            "body": (
                "The animal subject to this contract is described below. "
                "The adopter acknowledges having verified the animal's health status "
                "before signing this contract."
            ),
        },
        {
            "id": "2",
            "title": "Adopter Identification",
            "title_es": "Identificacion del Adoptante",
            "fields": ["full_name", "id_or_passport", "address", "phone", "email"],
            "body": (
                "The adopter declares being of legal age and having full legal capacity "
                "to enter into this contract under applicable Paraguayan law."
            ),
        },
        {
            "id": "3",
            "title": "Vaccination History",
            "title_es": "Historial de Vacunacion",
            "fields": ["rabies_vaccine", "rabies_date", "other_vaccines"],
            "body": (
                "In accordance with Ley 3140/2006, the animal has a current rabies vaccination. "
                "The adopter commits to keeping the vaccination schedule up to date. "
                "Rabies vaccination is mandatory under national law."
            ),
            "legal_ref": "Ley 3140/2006, Art. 5",
        },
        {
            "id": "4",
            "title": "Sterilization Clause",
            "title_es": "Clausula de Esterilizacion",
            "fields": ["already_sterilized", "sterilization_commitment", "sterilization_deadline"],
            "body": (
                "If the animal has not been sterilized at the time of adoption, "
                "the adopter commits to having it sterilized within the stated deadline. "
                "Failure to comply with this clause may result in contract termination."
            ),
        },
        {
            "id": "5",
            "title": "Return Policy",
            "title_es": "Politica de Devolucion",
            "body": (
                "The adopter commits to returning the animal to Refugio Animal Paraguay "
                "if unable to continue with the adoption. Abandonment of the animal in any "
                "public or private space is strictly prohibited under Ley 4840/2013."
            ),
            "legal_ref": "Ley 4840/2013, Art. 8",
        },
        {
            "id": "6",
            "title": "Home Inspection Clause",
            "title_es": "Clausula de Inspeccion del Hogar",
            "body": (
                "Refugio Animal Paraguay reserves the right to conduct follow-up visits "
                "to the adopter's home to verify the animal's living conditions. "
                "The adopter authorizes such visits with 48 hours' advance notice."
            ),
        },
        {
            "id": "7",
            "title": "Prohibition on Resale or Transfer",
            "title_es": "Prohibicion de Reventa o Transferencia",
            "body": (
                "The adopter acknowledges that the animal is a living being and not a commercial commodity. "
                "The sale, assignment, or transfer of the animal to third parties is expressly prohibited "
                "without prior written authorization from Refugio Animal Paraguay."
            ),
        },
        {
            "id": "8",
            "title": "Animal Welfare Obligations",
            "title_es": "Obligaciones de Bienestar Animal",
            "body": (
                "The adopter commits to: (a) providing adequate food and fresh water; "
                "(b) ensuring veterinary care in case of illness or injury; "
                "(c) not subjecting the animal to physical or psychological mistreatment; "
                "(d) complying with all provisions of Ley 4840/2013 on Animal Welfare."
            ),
            "legal_ref": "Ley 4840/2013, Art. 3-7",
        },
        {
            "id": "9",
            "title": "Microchip Acknowledgment",
            "title_es": "Reconocimiento de Microchip",
            "fields": ["microchip_number"],
            "body": (
                "If the animal has an identification microchip, the adopter acknowledges "
                "the registered number and commits not to alter, remove, or disable the device. "
                "The microchip is the animal's official identification."
            ),
        },
        {
            "id": "10",
            "title": "Governing Law and Jurisdiction",
            "title_es": "Ley Aplicable y Jurisdiccion",
            "body": (
                "This contract is governed by the laws of the Republic of Paraguay, "
                "particularly Ley 4840/2013 and Ley 3140/2006. "
                "Any dispute arising from this contract shall be submitted to the "
                "competent courts of Asuncion, Paraguay."
            ),
        },
    ],
    "signature_fields": [
        {
            "party": "adopter",
            "label": "Adopter",
            "name": None,
            "id_number": None,
            "date": None,
            "signature": None,
        },
        {
            "party": "shelter",
            "label": "Refugio Animal Paraguay Representative",
            "name": None,
            "title": None,
            "date": None,
            "signature": None,
        },
    ],
    "contact": "adopciones@refugioanimal.com.py",
}

_SUPPORTED_LANGUAGES = {"es", "en"}


@router.get("/adoption-contract", summary="Paraguayan adoption contract template")
async def get_adoption_contract_template(
    lang: str = Query(
        default="es",
        description="Template language: 'es' (Spanish, default) or 'en' (English)",
    ),
) -> dict:
    """Return the Paraguayan animal adoption contract template.

    The template reflects the requirements of:
    - Ley 4840/2013 (Animal Welfare Law)
    - Ley 3140/2006 (Animal Disease Control — mandatory rabies vaccination)
    - Decreto 1237 (SENACSA veterinary registry)

    Use ?lang=en for the English version.
    Signature fields are blank — fill in per individual adoption.
    """
    resolved_lang = lang.lower() if lang.lower() in _SUPPORTED_LANGUAGES else "es"
    template = _ADOPTION_CONTRACT_EN if resolved_lang == "en" else _ADOPTION_CONTRACT_ES
    return {
        **template,
        "version": "1.0",
        "last_updated": ADOPTION_CONTRACT_LAST_UPDATED,
        "language": resolved_lang,
        "shelter": {
            "name": "Refugio Animal Paraguay",
            "address": "Asuncion, Paraguay",
            "contact": "adopciones@refugioanimal.com.py",
        },
    }


# ---------------------------------------------------------------------------
# Paraguayan record retention policy (RAP-247)
# ---------------------------------------------------------------------------

RETENTION_POLICY_LAST_UPDATED = date(2026, 3, 29).isoformat()


@router.get("/record-retention-policy", summary="Paraguayan record retention policy")
async def get_record_retention_policy(
    lang: str = Query(
        default="es",
        description="Document language: 'es' (Spanish, default) or 'en' (English). Unsupported codes fall back to 'es'.",
    ),
) -> dict:
    """Return the mandatory record retention periods per Paraguayan law.

    Available in Spanish (es, default) and English (en). Covers:
    - Adoption contracts (Codigo Civil Art. 633): 10 years
    - Animal health records (Ley 4840/2013): 5 years
    - Vaccination records (Ley 3140/2006): 5 years
    - Donation/financial records (Ley 125/91): 5 years
    - Adopter personal data: 5 years
    - General correspondence: 2 years

    These are minimum retention periods. The shelter may retain records longer.
    """
    resolved = normalise_language(lang)
    if resolved == "es":
        document_title = RETENTION_POLICY_DOCUMENT_TITLE_ES
        note = RETENTION_POLICY_SUMMARY_ES
    else:
        document_title = "Paraguayan Record Retention Policy"
        note = (
            "These are minimum mandatory retention periods under Paraguayan law. "
            "The shelter may retain records for longer periods at its discretion."
        )
    return {
        "document": document_title,
        "version": "1.0",
        "language": resolved,
        "last_updated": RETENTION_POLICY_LAST_UPDATED,
        "jurisdiction": "Republic of Paraguay",
        "note": note,
        "policies": RETENTION_POLICY,
    }
