"""Rescuer directory API for donor choice interface.

Public directory of verified rescuers that donors can browse, search,
filter, and choose to support. Supports location, specialty, and
impact-based filtering with multiple sort options.

Endpoints:
    GET /api/rescuers            -- list verified rescuers (public)
    GET /api/rescuers/{id}       -- get rescuer profile details
    GET /api/rescuers/{id}/impact -- get rescuer impact statistics
"""

import logging
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rescuers",
    tags=["rescuer-directory"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 48
DEFAULT_SORT = "activity"


class RescuerSpecialty(StrEnum):
    """Rescuer specialties."""

    DOGS = "dogs"
    CATS = "cats"
    MIXED = "mixed"
    EXOTIC = "exotic"
    FARM = "farm"
    WILDLIFE = "wildlife"


class SortOption(StrEnum):
    """Sort options for directory."""

    ACTIVITY = "activity"
    SUPPORTERS = "supporters"
    ANIMALS_RESCUED = "animals_rescued"
    NAME = "name"


SPECIALTY_LABELS_ES: dict[str, str] = {
    "dogs": "Perros",
    "cats": "Gatos",
    "mixed": "Mixto",
    "exotic": "Exotico",
    "farm": "Granja",
    "wildlife": "Fauna silvestre",
}

SORT_LABELS_ES: dict[str, str] = {
    "activity": "Actividad reciente",
    "supporters": "Mas apoyados",
    "animals_rescued": "Mas rescates",
    "name": "Nombre",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class RescuerCard(BaseModel):
    """Rescuer summary for directory listing."""

    id: str
    name: str
    location: str
    specialty: RescuerSpecialty
    specialty_label: str
    mission: str
    animals_rescued: int
    supporter_count: int
    is_verified: bool
    profile_photo_url: str | None = None
    last_active: str


class RescuerListResponse(BaseModel):
    """Paginated rescuer directory."""

    rescuers: list[RescuerCard]
    total: int
    page: int
    page_size: int
    sort: SortOption


class RescuerProfile(BaseModel):
    """Full rescuer profile."""

    id: str
    name: str
    location: str
    specialty: RescuerSpecialty
    specialty_label: str
    mission: str
    bio: str
    animals_rescued: int
    animals_currently: int
    supporter_count: int
    is_verified: bool
    profile_photo_url: str | None
    contact_email: str
    social_links: dict[str, str]
    joined_date: str
    last_active: str
    recent_rescues: list[dict[str, Any]]


class RescuerImpact(BaseModel):
    """Rescuer impact statistics."""

    rescuer_id: str
    total_rescued: int
    total_adopted: int
    total_fostered: int
    total_sterilized: int
    monthly_rescues: list[dict[str, Any]]
    species_breakdown: list[dict[str, Any]]
    community_rating: float


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_RESCUERS: list[dict[str, Any]] = [
    {
        "id": "rsc-001",
        "name": "Ana Lopez Rescates",
        "location": "Asuncion Centro",
        "specialty": RescuerSpecialty.DOGS,
        "mission": "Rescatamos y rehabilitamos perros callejeros en Asuncion",
        "bio": "Desde 2018 dedicada al rescate de perros en situacion de calle.",
        "animals_rescued": 245,
        "animals_currently": 18,
        "supporter_count": 87,
        "is_verified": True,
        "contact_email": "ana@rescates.py",
        "social_links": {"instagram": "@ana_rescates", "facebook": "AnaRescates"},
        "joined_date": "2018-03-15",
        "last_active": "2026-03-27",
    },
    {
        "id": "rsc-002",
        "name": "Gatitos PY",
        "location": "San Lorenzo",
        "specialty": RescuerSpecialty.CATS,
        "mission": "Refugio especializado en gatos abandonados y colonias felinas",
        "bio": "Gestionamos 3 colonias felinas y un hogar de acogida.",
        "animals_rescued": 180,
        "animals_currently": 32,
        "supporter_count": 124,
        "is_verified": True,
        "contact_email": "info@gatitospy.com",
        "social_links": {"instagram": "@gatitospy"},
        "joined_date": "2019-06-01",
        "last_active": "2026-03-26",
    },
    {
        "id": "rsc-003",
        "name": "Refugio Esperanza",
        "location": "Luque",
        "specialty": RescuerSpecialty.MIXED,
        "mission": "Damos una segunda oportunidad a perros y gatos",
        "bio": "Refugio mixto con capacidad para 50 animales.",
        "animals_rescued": 320,
        "animals_currently": 45,
        "supporter_count": 156,
        "is_verified": True,
        "contact_email": "esperanza@refugio.py",
        "social_links": {"instagram": "@refugio_esperanza", "website": "www.refugioesperanza.py"},
        "joined_date": "2017-01-10",
        "last_active": "2026-03-28",
    },
    {
        "id": "rsc-004",
        "name": "Patitas Libres",
        "location": "Fernando de la Mora",
        "specialty": RescuerSpecialty.DOGS,
        "mission": "Rescate y esterilizacion de perros en barrios perifericos",
        "bio": "Enfocados en esterilizacion masiva y educacion comunitaria.",
        "animals_rescued": 410,
        "animals_currently": 12,
        "supporter_count": 203,
        "is_verified": True,
        "contact_email": "patitas@libres.py",
        "social_links": {"instagram": "@patitaslibres"},
        "joined_date": "2016-08-20",
        "last_active": "2026-03-25",
    },
    {
        "id": "rsc-005",
        "name": "Exoticos PY",
        "location": "Lambare",
        "specialty": RescuerSpecialty.EXOTIC,
        "mission": "Rescate de animales exoticos decomisados y abandonados",
        "bio": "Trabajamos con SEAM para rehabilitar fauna decomisada.",
        "animals_rescued": 65,
        "animals_currently": 8,
        "supporter_count": 42,
        "is_verified": True,
        "contact_email": "exoticos@py.com",
        "social_links": {},
        "joined_date": "2021-02-14",
        "last_active": "2026-03-20",
    },
    {
        "id": "rsc-006",
        "name": "Huellitas del Chaco",
        "location": "Chaco",
        "specialty": RescuerSpecialty.MIXED,
        "mission": "Rescate animal en comunidades rurales del Chaco",
        "bio": "Operamos en zonas remotas del Chaco paraguayo.",
        "animals_rescued": 95,
        "animals_currently": 22,
        "supporter_count": 38,
        "is_verified": True,
        "contact_email": "huellitas@chaco.py",
        "social_links": {"facebook": "HuellitasChaco"},
        "joined_date": "2020-05-01",
        "last_active": "2026-03-22",
    },
]


def _build_card(data: dict[str, Any]) -> RescuerCard:
    """Build card from rescuer data."""
    return RescuerCard(
        id=data["id"],
        name=data["name"],
        location=data["location"],
        specialty=data["specialty"],
        specialty_label=SPECIALTY_LABELS_ES.get(data["specialty"], data["specialty"]),
        mission=data["mission"],
        animals_rescued=data["animals_rescued"],
        supporter_count=data["supporter_count"],
        is_verified=data["is_verified"],
        profile_photo_url=None,
        last_active=data["last_active"],
    )


def _build_profile(data: dict[str, Any]) -> RescuerProfile:
    """Build full profile from rescuer data."""
    return RescuerProfile(
        id=data["id"],
        name=data["name"],
        location=data["location"],
        specialty=data["specialty"],
        specialty_label=SPECIALTY_LABELS_ES.get(data["specialty"], data["specialty"]),
        mission=data["mission"],
        bio=data["bio"],
        animals_rescued=data["animals_rescued"],
        animals_currently=data["animals_currently"],
        supporter_count=data["supporter_count"],
        is_verified=data["is_verified"],
        profile_photo_url=None,
        contact_email=data["contact_email"],
        social_links=data["social_links"],
        joined_date=data["joined_date"],
        last_active=data["last_active"],
        recent_rescues=[
            {"name": "Luna", "species": "Perro", "date": "2026-03-20"},
            {"name": "Michi", "species": "Gato", "date": "2026-03-15"},
        ],
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=RescuerListResponse)
async def list_rescuers(
    search: str | None = None,
    specialty: RescuerSpecialty | None = None,
    location: str | None = None,
    sort: SortOption = Query(SortOption.ACTIVITY),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> RescuerListResponse:
    """List verified rescuers (public directory)."""
    rescuers = [r for r in SAMPLE_RESCUERS if r["is_verified"]]

    if search:
        rescuers = [r for r in rescuers if search.lower() in r["name"].lower()]
    if specialty:
        rescuers = [r for r in rescuers if r["specialty"] == specialty]
    if location:
        rescuers = [r for r in rescuers if location.lower() in r["location"].lower()]

    sort_keys = {
        SortOption.ACTIVITY: lambda r: r["last_active"],
        SortOption.SUPPORTERS: lambda r: r["supporter_count"],
        SortOption.ANIMALS_RESCUED: lambda r: r["animals_rescued"],
        SortOption.NAME: lambda r: r["name"].lower(),
    }
    reverse = sort != SortOption.NAME
    rescuers.sort(key=sort_keys.get(sort, sort_keys[SortOption.ACTIVITY]), reverse=reverse)

    total = len(rescuers)
    start = (page - 1) * page_size
    page_rescuers = rescuers[start : start + page_size]

    return RescuerListResponse(
        rescuers=[_build_card(r) for r in page_rescuers],
        total=total,
        page=page,
        page_size=page_size,
        sort=sort,
    )


@router.get("/{rescuer_id}", response_model=RescuerProfile)
async def get_rescuer_profile(rescuer_id: str) -> RescuerProfile:
    """Get full rescuer profile."""
    for r in SAMPLE_RESCUERS:
        if r["id"] == rescuer_id:
            return _build_profile(r)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Rescuer '{rescuer_id}' not found",
    )


@router.get("/{rescuer_id}/impact", response_model=RescuerImpact)
async def get_rescuer_impact(rescuer_id: str) -> RescuerImpact:
    """Get rescuer impact statistics."""
    found = None
    for r in SAMPLE_RESCUERS:
        if r["id"] == rescuer_id:
            found = r
            break
    if found is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rescuer '{rescuer_id}' not found",
        )

    return RescuerImpact(
        rescuer_id=rescuer_id,
        total_rescued=found["animals_rescued"],
        total_adopted=int(found["animals_rescued"] * 0.7),
        total_fostered=int(found["animals_rescued"] * 0.15),
        total_sterilized=int(found["animals_rescued"] * 0.9),
        monthly_rescues=[
            {"month": "2026-01", "count": 8},
            {"month": "2026-02", "count": 12},
            {"month": "2026-03", "count": 10},
        ],
        species_breakdown=[
            {"species": "Perros", "count": int(found["animals_rescued"] * 0.6)},
            {"species": "Gatos", "count": int(found["animals_rescued"] * 0.35)},
            {"species": "Otros", "count": int(found["animals_rescued"] * 0.05)},
        ],
        community_rating=4.7,
    )
