"""Multilingual support for legal document endpoints (RAP-249).

Provides Spanish (es) and English (en) translations for all legal documents
served by the /legal/* API endpoints. Spanish is the official language of
Paraguay and serves as the default for legally binding documents. English
is provided for EU donors and international partners.

Supported documents:
  - dpa                    (Data Processing Agreement)
  - record-retention-policy (Paraguayan record retention summary)
  - sub-processors         (Sub-processor registry)
"""

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: frozenset[str] = frozenset({"es", "en"})

DEFAULT_LANGUAGE: str = "es"

LANGUAGE_NAMES: dict[str, str] = {
    "es": "Español",
    "en": "English",
}

# Documents that have multi-language support
MULTILINGUAL_DOCUMENTS: list[dict] = [
    {
        "document_key": "dpa",
        "endpoint": "/legal/dpa",
        "title_en": "Data Processing Agreement",
        "title_es": "Acuerdo de Procesamiento de Datos",
        "supported_languages": ["es", "en"],
    },
    {
        "document_key": "record-retention-policy",
        "endpoint": "/legal/record-retention-policy",
        "title_en": "Record Retention Policy",
        "title_es": "Política de Retención de Registros",
        "supported_languages": ["es", "en"],
    },
    {
        "document_key": "sub-processors",
        "endpoint": "/legal/sub-processors",
        "title_en": "Sub-processor Registry",
        "title_es": "Registro de Sub-procesadores",
        "supported_languages": ["es", "en"],
    },
]


# ---------------------------------------------------------------------------
# Spanish DPA sections
# ---------------------------------------------------------------------------

DPA_SECTIONS_ES: list[dict] = [
    {
        "id": "1",
        "title": "Objeto y duración",
        "body": (
            "Este Acuerdo de Procesamiento de Datos (APD) regula el tratamiento de datos personales "
            "por parte del Procesador en nombre del Responsable conforme al acuerdo de servicios principal. "
            "El APD estará vigente durante la duración del acuerdo de servicios y se extinguirá "
            "automáticamente al vencer o resolverse dicho acuerdo."
        ),
    },
    {
        "id": "2",
        "title": "Naturaleza y finalidad del tratamiento",
        "body": (
            "El Procesador únicamente podrá tratar datos personales para los fines específicos definidos en el "
            "acuerdo de servicios (por ejemplo, atención veterinaria, coordinación de voluntarios, "
            "procesamiento de donaciones). Cualquier tratamiento con otra finalidad requerirá "
            "consentimiento previo por escrito del Responsable."
        ),
    },
    {
        "id": "3",
        "title": "Categorías de interesados y datos personales",
        "body": (
            "Los interesados pueden incluir: donantes, adoptantes, voluntarios, rescatistas y personal del refugio. "
            "Las categorías de datos personales tratados pueden incluir: nombre, dirección de correo electrónico, "
            "número de teléfono, domicilio, datos de transacciones financieras (importes, referencias de pago) "
            "y, cuando corresponda, datos de salud animal bajo atención veterinaria."
        ),
    },
    {
        "id": "4",
        "title": "Obligaciones del Procesador",
        "body": (
            "El Procesador deberá: (a) tratar los datos personales únicamente conforme a instrucciones "
            "documentadas del Responsable; (b) garantizar que las personas autorizadas estén sujetas al deber "
            "de confidencialidad; (c) aplicar medidas técnicas y organizativas de seguridad adecuadas "
            "(Art. 32 RGPD); (d) asistir al Responsable en el cumplimiento de los derechos de los interesados; "
            "(e) suprimir o devolver todos los datos personales a la finalización; "
            "(f) poner a disposición la información necesaria para demostrar el cumplimiento."
        ),
    },
    {
        "id": "5",
        "title": "Sub-procesadores",
        "body": (
            "El Procesador no podrá contratar sub-procesadores sin autorización previa por escrito del Responsable. "
            "El Responsable podrá consultar el registro de sub-procesadores del refugio en /legal/sub-processors. "
            "El Procesador deberá imponer las mismas obligaciones de protección de datos a cualquier "
            "sub-procesador aprobado."
        ),
    },
    {
        "id": "6",
        "title": "Medidas de seguridad",
        "body": (
            "El Procesador deberá aplicar medidas que incluyan, entre otras: cifrado de datos personales "
            "en tránsito y en reposo; controles de acceso y autenticación; "
            "pruebas de seguridad periódicas; procedimientos para evaluar regularmente "
            "la eficacia de las medidas de seguridad."
        ),
    },
    {
        "id": "7",
        "title": "Notificación de violaciones de seguridad",
        "body": (
            "El Procesador notificará al Responsable sin demora indebida (en un plazo de 24 horas) "
            "tras tener conocimiento de una violación de seguridad de datos personales. "
            "La notificación incluirá: naturaleza de la violación, categorías y número aproximado "
            "de interesados afectados, consecuencias probables y medidas adoptadas o propuestas."
        ),
    },
    {
        "id": "8",
        "title": "Transferencias de datos",
        "body": (
            "Los datos personales solo podrán transferirse a terceros países fuera del EEE cuando se garantice "
            "un nivel de protección adecuado (por ejemplo, decisión de adecuación de la UE, Cláusulas "
            "Contractuales Tipo o normas corporativas vinculantes). El Procesador deberá notificar al "
            "Responsable cualquier transferencia transfronteriza prevista."
        ),
    },
    {
        "id": "9",
        "title": "Legislación aplicable",
        "body": (
            "El presente APD se rige por las leyes de la República del Paraguay y, cuando los interesados del "
            "Responsable se encuentren en la Unión Europea, también por el Reglamento (UE) 2016/679 (RGPD). "
            "Las controversias se someterán a los tribunales competentes de Asunción, Paraguay."
        ),
    },
]

# ---------------------------------------------------------------------------
# Spanish retention policy summary strings
# ---------------------------------------------------------------------------

RETENTION_POLICY_SUMMARY_ES: str = (
    "Estos son los períodos mínimos de retención obligatorios conforme a la legislación paraguaya. "
    "El refugio puede conservar los registros durante períodos más largos a su discreción."
)

RETENTION_POLICY_DOCUMENT_TITLE_ES: str = "Política de Retención de Registros — Paraguay"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def normalise_language(lang: str) -> str:
    """Normalise a language code to lowercase and fall back to default if unsupported.

    Args:
        lang: Raw language code from query param (e.g. 'ES', 'en', 'fr').

    Returns:
        Normalised code from SUPPORTED_LANGUAGES, or DEFAULT_LANGUAGE.
    """
    normalised = lang.strip().lower()
    if normalised in SUPPORTED_LANGUAGES:
        return normalised
    return DEFAULT_LANGUAGE
