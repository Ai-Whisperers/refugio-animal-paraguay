"""Public rescuer profile API.

Provides detailed rescuer profile data including bio, impact stats,
animals in care, campaigns, donor wall, and contact information.

Endpoints:
    GET /api/rescuers/{slug}/profile      -- full profile with all sections
    GET /api/rescuers/{slug}/animals      -- animals in care
    GET /api/rescuers/{slug}/campaigns    -- rescuer campaigns with progress
    GET /api/rescuers/{slug}/supporters   -- donor wall / supporters
    GET /api/rescuers/{slug}/contact      -- contact information
"""

import logging
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rescuers",
    tags=["rescuer-profile"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 50


class AdoptionStatus(StrEnum):
    """Animal adoption status."""

    AVAILABLE = "available"
    IN_PROCESS = "in_process"
    ADOPTED = "adopted"
    MEDICAL_HOLD = "medical_hold"


class CampaignProgressStatus(StrEnum):
    """Campaign progress status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class VerificationMethod(StrEnum):
    """How the rescuer was verified."""

    DOCUMENTS = "documents"
    SITE_VISIT = "site_visit"
    PARTNER_REFERRAL = "partner_referral"
    GOVERNMENT_REGISTRY = "government_registry"


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RescuerProfileHeader(BaseModel):
    """Basic profile information."""

    id: str
    slug: str
    display_name: str
    photo_url: str | None = None
    bio: str
    location: str
    is_verified: bool
    verification_method: VerificationMethod | None = None
    verified_since: str | None = None
    joined_date: str
    social_links: dict[str, str] = Field(default_factory=dict)


class ImpactStats(BaseModel):
    """Rescuer impact statistics."""

    animals_rescued: int
    animals_adopted: int
    animals_sterilized: int
    financial_support_received_pyg: int
    active_supporters: int
    years_active: float


class AnimalCard(BaseModel):
    """Animal in care card."""

    id: str
    name: str
    species: str
    breed: str
    age: str
    photo_url: str | None = None
    adoption_status: AdoptionStatus
    rescue_date: str
    description: str


class AnimalListResponse(BaseModel):
    """Paginated animal list."""

    animals: list[AnimalCard]
    total: int
    page: int
    page_size: int


class CampaignCard(BaseModel):
    """Campaign with progress."""

    id: str
    title: str
    description: str
    goal_amount: float
    raised_amount: float
    currency: str
    progress_pct: float
    status: CampaignProgressStatus
    supporter_count: int
    created_at: str
    end_date: str | None = None


class CampaignListResponse(BaseModel):
    """Campaign list."""

    campaigns: list[CampaignCard]
    total: int


class Supporter(BaseModel):
    """Donor wall entry."""

    id: str
    display_name: str
    is_anonymous: bool
    amount: float | None = None
    currency: str | None = None
    message: str | None = None
    supported_since: str
    is_monthly: bool


class SupporterListResponse(BaseModel):
    """Paginated supporter list."""

    supporters: list[Supporter]
    total: int
    total_monthly: int


class ContactInfo(BaseModel):
    """Rescuer contact information."""

    email: str | None = None
    whatsapp: str | None = None
    phone: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None
    website_url: str | None = None
    accepts_messages: bool = True


class DonationOption(BaseModel):
    """Donation option for support button."""

    label: str
    amount: float
    currency: str
    is_monthly: bool


class SupportOptions(BaseModel):
    """Available support options."""

    donation_options: list[DonationOption]
    accepts_monthly: bool
    custom_amount_allowed: bool


class FullProfile(BaseModel):
    """Complete rescuer profile."""

    header: RescuerProfileHeader
    impact: ImpactStats
    animals_preview: list[AnimalCard]
    campaigns: list[CampaignCard]
    support_options: SupportOptions
    contact: ContactInfo


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_PROFILES: dict[str, dict[str, Any]] = {
    "carlos-mendoza": {
        "header": {
            "id": "resc-001",
            "slug": "carlos-mendoza",
            "display_name": "Carlos Mendoza",
            "photo_url": "/images/rescuers/carlos.jpg",
            "bio": "Rescatista dedicado desde 2020. Especializado en perros callejeros en el area metropolitana de Asuncion. Trabajo con veterinarios locales para esterilizacion y vacunacion.",
            "location": "Asuncion, Paraguay",
            "is_verified": True,
            "verification_method": VerificationMethod.SITE_VISIT,
            "verified_since": "2025-08-01",
            "joined_date": "2020-03-15",
            "social_links": {
                "facebook": "https://facebook.com/carlos.rescate",
                "instagram": "https://instagram.com/carlos_rescate_py",
            },
        },
        "impact": {
            "animals_rescued": 127,
            "animals_adopted": 89,
            "animals_sterilized": 203,
            "financial_support_received_pyg": 45000000,
            "active_supporters": 45,
            "years_active": 6.0,
        },
        "animals": [
            {
                "id": "ani-001",
                "name": "Luna",
                "species": "Perro",
                "breed": "Mestizo",
                "age": "3 anos",
                "photo_url": "/images/animals/luna.jpg",
                "adoption_status": AdoptionStatus.AVAILABLE,
                "rescue_date": "2026-01-15",
                "description": "Luna es una perra cariñosa rescatada de la calle. Ideal para familias.",
            },
            {
                "id": "ani-002",
                "name": "Rocky",
                "species": "Perro",
                "breed": "Pastor Aleman Mix",
                "age": "4 anos",
                "photo_url": "/images/animals/rocky.jpg",
                "adoption_status": AdoptionStatus.IN_PROCESS,
                "rescue_date": "2025-11-20",
                "description": "Rocky fue encontrado herido. Ahora esta sano y listo para un hogar.",
            },
            {
                "id": "ani-003",
                "name": "Michi",
                "species": "Gato",
                "breed": "Siames Mix",
                "age": "2 anos",
                "photo_url": "/images/animals/michi.jpg",
                "adoption_status": AdoptionStatus.AVAILABLE,
                "rescue_date": "2026-02-10",
                "description": "Gato jugueton y sociable. Se lleva bien con otros gatos.",
            },
            {
                "id": "ani-004",
                "name": "Nala",
                "species": "Perro",
                "breed": "Labrador Mix",
                "age": "1 ano",
                "photo_url": "/images/animals/nala.jpg",
                "adoption_status": AdoptionStatus.AVAILABLE,
                "rescue_date": "2026-03-01",
                "description": "Cachorra energetica. Necesita espacio para correr.",
            },
            {
                "id": "ani-005",
                "name": "Simba",
                "species": "Gato",
                "breed": "Naranja Comun",
                "age": "5 anos",
                "photo_url": "/images/animals/simba.jpg",
                "adoption_status": AdoptionStatus.ADOPTED,
                "rescue_date": "2025-09-15",
                "description": "Simba encontro su hogar definitivo.",
            },
            {
                "id": "ani-006",
                "name": "Thor",
                "species": "Perro",
                "breed": "Pitbull Mix",
                "age": "3 anos",
                "photo_url": "/images/animals/thor.jpg",
                "adoption_status": AdoptionStatus.MEDICAL_HOLD,
                "rescue_date": "2026-03-10",
                "description": "En tratamiento veterinario. Pronto disponible.",
            },
        ],
        "campaigns": [
            {
                "id": "camp-001",
                "title": "Esterilizacion masiva Barrio Obrero",
                "description": "Campana para esterilizar 50 animales callejeros en Barrio Obrero",
                "goal_amount": 5000000,
                "raised_amount": 3250000,
                "currency": "PYG",
                "progress_pct": 65.0,
                "status": CampaignProgressStatus.ACTIVE,
                "supporter_count": 23,
                "created_at": "2026-02-01",
                "end_date": "2026-04-30",
            },
            {
                "id": "camp-002",
                "title": "Refugio temporal zona Norte",
                "description": "Construir refugio temporal para 20 animales rescatados de inundaciones",
                "goal_amount": 8000000,
                "raised_amount": 8000000,
                "currency": "PYG",
                "progress_pct": 100.0,
                "status": CampaignProgressStatus.COMPLETED,
                "supporter_count": 41,
                "created_at": "2025-10-01",
                "end_date": "2025-12-31",
            },
        ],
        "supporters": [
            {
                "id": "sup-001",
                "display_name": "Maria Garcia",
                "is_anonymous": False,
                "amount": 500000,
                "currency": "PYG",
                "message": "Gracias por tu trabajo Carlos!",
                "supported_since": "2025-06-01",
                "is_monthly": True,
            },
            {
                "id": "sup-002",
                "display_name": "Anonimo",
                "is_anonymous": True,
                "amount": None,
                "currency": None,
                "message": None,
                "supported_since": "2025-08-15",
                "is_monthly": True,
            },
            {
                "id": "sup-003",
                "display_name": "Hans Mueller",
                "is_anonymous": False,
                "amount": 100,
                "currency": "EUR",
                "message": "Supporting from Germany",
                "supported_since": "2026-01-10",
                "is_monthly": False,
            },
            {
                "id": "sup-004",
                "display_name": "Juan Perez",
                "is_anonymous": False,
                "amount": 200000,
                "currency": "PYG",
                "message": None,
                "supported_since": "2026-02-20",
                "is_monthly": False,
            },
            {
                "id": "sup-005",
                "display_name": "Anna Schmidt",
                "is_anonymous": False,
                "amount": 50,
                "currency": "EUR",
                "message": "Keep up the great work!",
                "supported_since": "2026-03-01",
                "is_monthly": True,
            },
        ],
        "contact": {
            "email": "carlos@rescate.py",
            "whatsapp": "+595981234567",
            "phone": "+595981234567",
            "facebook_url": "https://facebook.com/carlos.rescate",
            "instagram_url": "https://instagram.com/carlos_rescate_py",
            "website_url": None,
            "accepts_messages": True,
        },
        "support_options": {
            "donation_options": [
                {
                    "label": "Alimento para 1 semana",
                    "amount": 50000,
                    "currency": "PYG",
                    "is_monthly": False,
                },
                {
                    "label": "Vacunacion completa",
                    "amount": 150000,
                    "currency": "PYG",
                    "is_monthly": False,
                },
                {
                    "label": "Esterilizacion",
                    "amount": 300000,
                    "currency": "PYG",
                    "is_monthly": False,
                },
                {"label": "Apoyo mensual", "amount": 100000, "currency": "PYG", "is_monthly": True},
                {
                    "label": "Monthly support (EU)",
                    "amount": 10,
                    "currency": "EUR",
                    "is_monthly": True,
                },
            ],
            "accepts_monthly": True,
            "custom_amount_allowed": True,
        },
    },
    "laura-gimenez": {
        "header": {
            "id": "resc-004",
            "slug": "laura-gimenez",
            "display_name": "Laura Gimenez",
            "photo_url": "/images/rescuers/laura.jpg",
            "bio": "Fundadora de Refugio Esperanza. Mas de 10 anos rescatando animales en Asuncion y alrededores.",
            "location": "Asuncion, Paraguay",
            "is_verified": True,
            "verification_method": VerificationMethod.GOVERNMENT_REGISTRY,
            "verified_since": "2025-04-15",
            "joined_date": "2016-01-10",
            "social_links": {
                "facebook": "https://facebook.com/refugio.esperanza",
                "instagram": "https://instagram.com/refugio_esperanza_py",
            },
        },
        "impact": {
            "animals_rescued": 312,
            "animals_adopted": 245,
            "animals_sterilized": 410,
            "financial_support_received_pyg": 120000000,
            "active_supporters": 67,
            "years_active": 10.2,
        },
        "animals": [
            {
                "id": "ani-101",
                "name": "Canela",
                "species": "Perro",
                "breed": "Mestizo",
                "age": "2 anos",
                "photo_url": None,
                "adoption_status": AdoptionStatus.AVAILABLE,
                "rescue_date": "2026-02-20",
                "description": "Perra dulce y tranquila. Ideal para departamento.",
            },
        ],
        "campaigns": [],
        "supporters": [
            {
                "id": "sup-010",
                "display_name": "Pedro Lopez",
                "is_anonymous": False,
                "amount": 300000,
                "currency": "PYG",
                "message": "Excelente labor Laura",
                "supported_since": "2025-01-15",
                "is_monthly": True,
            },
        ],
        "contact": {
            "email": "laura@refugio.py",
            "whatsapp": "+595987654321",
            "phone": None,
            "facebook_url": "https://facebook.com/refugio.esperanza",
            "instagram_url": "https://instagram.com/refugio_esperanza_py",
            "website_url": "https://refugioesperanza.com.py",
            "accepts_messages": True,
        },
        "support_options": {
            "donation_options": [
                {
                    "label": "Alimento mensual",
                    "amount": 100000,
                    "currency": "PYG",
                    "is_monthly": True,
                },
                {"label": "Vacunacion", "amount": 200000, "currency": "PYG", "is_monthly": False},
            ],
            "accepts_monthly": True,
            "custom_amount_allowed": True,
        },
    },
}

PROFILE_SLUGS = list(SAMPLE_PROFILES.keys())


def _get_profile_data(slug: str) -> dict[str, Any]:
    """Get profile data or raise 404."""
    if slug not in SAMPLE_PROFILES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rescuer '{slug}' not found",
        )
    return SAMPLE_PROFILES[slug]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/{slug}/profile", response_model=FullProfile)
async def get_full_profile(slug: str) -> FullProfile:
    """Get complete rescuer profile."""
    data = _get_profile_data(slug)
    animals_preview = [AnimalCard(**a) for a in data["animals"][:4]]

    return FullProfile(
        header=RescuerProfileHeader(**data["header"]),
        impact=ImpactStats(**data["impact"]),
        animals_preview=animals_preview,
        campaigns=[CampaignCard(**c) for c in data["campaigns"]],
        support_options=SupportOptions(**data["support_options"]),
        contact=ContactInfo(**data["contact"]),
    )


@router.get("/{slug}/animals", response_model=AnimalListResponse)
async def get_rescuer_animals(
    slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    adoption_status: AdoptionStatus | None = None,
) -> AnimalListResponse:
    """Get animals in rescuer's care."""
    data = _get_profile_data(slug)
    animals = data["animals"]

    if adoption_status:
        animals = [a for a in animals if a["adoption_status"] == adoption_status]

    total = len(animals)
    start = (page - 1) * page_size
    page_items = animals[start : start + page_size]

    return AnimalListResponse(
        animals=[AnimalCard(**a) for a in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{slug}/campaigns", response_model=CampaignListResponse)
async def get_rescuer_campaigns(slug: str) -> CampaignListResponse:
    """Get rescuer's campaigns with progress."""
    data = _get_profile_data(slug)
    campaigns = [CampaignCard(**c) for c in data["campaigns"]]

    return CampaignListResponse(campaigns=campaigns, total=len(campaigns))


@router.get("/{slug}/supporters", response_model=SupporterListResponse)
async def get_supporters(
    slug: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> SupporterListResponse:
    """Get rescuer's supporter/donor wall."""
    data = _get_profile_data(slug)
    supporters = data["supporters"]
    total = len(supporters)
    total_monthly = sum(1 for s in supporters if s["is_monthly"])

    start = (page - 1) * page_size
    page_items = supporters[start : start + page_size]

    return SupporterListResponse(
        supporters=[Supporter(**s) for s in page_items],
        total=total,
        total_monthly=total_monthly,
    )


@router.get("/{slug}/contact", response_model=ContactInfo)
async def get_contact_info(slug: str) -> ContactInfo:
    """Get rescuer's contact information."""
    data = _get_profile_data(slug)
    return ContactInfo(**data["contact"])
