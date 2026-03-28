"""Rescuer animal listing management API.

Allows rescuers to add, manage, and list animals they are rescuing.
Provides both a portal interface for rescuers and a public listing.

Endpoints:
    GET    /api/portal/rescuer/animals           -- list rescuer's animals
    POST   /api/portal/rescuer/animals           -- add new animal
    GET    /api/portal/rescuer/animals/{id}      -- get animal details
    PUT    /api/portal/rescuer/animals/{id}      -- edit animal
    PATCH  /api/portal/rescuer/animals/{id}/status  -- change status
    DELETE /api/portal/rescuer/animals/{id}      -- soft-delete (archive)
    POST   /api/portal/rescuer/animals/{id}/story   -- add adoption story
    GET    /api/rescuers/{slug}/animals          -- public listing
"""

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

portal_router = APIRouter(
    prefix="/api/portal/rescuer/animals",
    tags=["rescuer-animals-portal"],
)

public_router = APIRouter(
    prefix="/api/rescuers",
    tags=["rescuer-animals-public"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 50
MAX_PHOTOS_PER_ANIMAL = 5
MIN_DESCRIPTION_LENGTH = 10
MAX_DESCRIPTION_LENGTH = 500


class Species(StrEnum):
    """Animal species."""

    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class UrgencyLevel(StrEnum):
    """Urgency level for animal needs."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnimalStatus(StrEnum):
    """Animal status in the system."""

    AVAILABLE = "available"
    ADOPTED = "adopted"
    IN_TREATMENT = "in_treatment"
    DECEASED = "deceased"
    ARCHIVED = "archived"


URGENCY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}

SPECIES_LABELS_ES: dict[str, str] = {
    "dog": "Perro",
    "cat": "Gato",
    "other": "Otro",
}

URGENCY_LABELS_ES: dict[str, str] = {
    "critical": "Critico",
    "high": "Alto",
    "medium": "Medio",
    "low": "Bajo",
}

STATUS_LABELS_ES: dict[str, str] = {
    "available": "Disponible",
    "adopted": "Adoptado",
    "in_treatment": "En tratamiento",
    "deceased": "Fallecido",
    "archived": "Archivado",
}

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "available": ["adopted", "in_treatment", "deceased", "archived"],
    "in_treatment": ["available", "deceased", "archived"],
    "adopted": ["available", "archived"],
    "deceased": ["archived"],
    "archived": [],
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AnimalCreateRequest(BaseModel):
    """Request to add a new animal."""

    name: str = Field(min_length=1, max_length=100)
    species: Species
    breed: str = Field(default="Mestizo", max_length=100)
    age: str = Field(max_length=50)
    description: str = Field(min_length=MIN_DESCRIPTION_LENGTH, max_length=MAX_DESCRIPTION_LENGTH)
    medical_needs: str = Field(default="", max_length=1000)
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    photo_urls: list[str] = Field(default_factory=lambda: ["/images/placeholder.jpg"])


class AnimalUpdateRequest(BaseModel):
    """Request to update an animal."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    species: Species | None = None
    breed: str | None = Field(default=None, max_length=100)
    age: str | None = Field(default=None, max_length=50)
    description: str | None = Field(
        default=None,
        min_length=MIN_DESCRIPTION_LENGTH,
        max_length=MAX_DESCRIPTION_LENGTH,
    )
    medical_needs: str | None = Field(default=None, max_length=1000)
    urgency: UrgencyLevel | None = None
    photo_urls: list[str] | None = None


class StatusChangeRequest(BaseModel):
    """Request to change animal status."""

    new_status: AnimalStatus
    reason: str = Field(default="", max_length=500)


class AdoptionStoryRequest(BaseModel):
    """Request to add an adoption story."""

    story_text: str = Field(min_length=10, max_length=2000)
    photo_url: str | None = None
    adopter_name: str | None = Field(default=None, max_length=100)


class RescuerAnimal(BaseModel):
    """Full animal record."""

    id: str
    rescuer_id: str
    name: str
    species: Species
    breed: str
    age: str
    description: str
    medical_needs: str
    urgency: UrgencyLevel
    status: AnimalStatus
    photo_urls: list[str]
    created_at: str
    updated_at: str
    adoption_story: dict[str, Any] | None = None


class AnimalListResponse(BaseModel):
    """Paginated animal list."""

    animals: list[RescuerAnimal]
    total: int
    page: int
    page_size: int


class PublicAnimalCard(BaseModel):
    """Public-facing animal card."""

    id: str
    name: str
    species: str
    species_label: str
    breed: str
    age: str
    description: str
    medical_needs: str
    urgency: UrgencyLevel
    urgency_label: str
    photo_url: str | None
    rescue_date: str


class PublicAnimalListResponse(BaseModel):
    """Public animal listing."""

    animals: list[PublicAnimalCard]
    total: int
    rescuer_name: str


class AnimalActionResponse(BaseModel):
    """Response after an animal action."""

    success: bool
    message: str
    animal_id: str


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

_animals: dict[str, dict[str, Any]] = {}

SAMPLE_ANIMALS: list[dict[str, Any]] = [
    {
        "id": "ranim-001",
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": "Luna",
        "species": Species.DOG,
        "breed": "Mestizo",
        "age": "3 anos",
        "description": "Perra cariñosa rescatada de la calle. Esterilizada y vacunada. Ideal para familias con niños.",
        "medical_needs": "",
        "urgency": UrgencyLevel.LOW,
        "status": AnimalStatus.AVAILABLE,
        "photo_urls": ["/images/animals/luna1.jpg", "/images/animals/luna2.jpg"],
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-03-20T14:00:00Z",
        "adoption_story": None,
    },
    {
        "id": "ranim-002",
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": "Rocky",
        "species": Species.DOG,
        "breed": "Pastor Aleman Mix",
        "age": "4 anos",
        "description": "Rescatado con heridas graves. Ahora completamente recuperado y buscando hogar definitivo.",
        "medical_needs": "Necesita medicacion mensual para articulaciones",
        "urgency": UrgencyLevel.MEDIUM,
        "status": AnimalStatus.AVAILABLE,
        "photo_urls": ["/images/animals/rocky1.jpg"],
        "created_at": "2025-11-20T08:00:00Z",
        "updated_at": "2026-03-15T09:00:00Z",
        "adoption_story": None,
    },
    {
        "id": "ranim-003",
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": "Michi",
        "species": Species.CAT,
        "breed": "Siames Mix",
        "age": "2 anos",
        "description": "Gato jugueton y sociable. Se lleva bien con otros gatos y perros tranquilos.",
        "medical_needs": "",
        "urgency": UrgencyLevel.LOW,
        "status": AnimalStatus.AVAILABLE,
        "photo_urls": ["/images/animals/michi1.jpg"],
        "created_at": "2026-02-10T12:00:00Z",
        "updated_at": "2026-03-18T11:00:00Z",
        "adoption_story": None,
    },
    {
        "id": "ranim-004",
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": "Thor",
        "species": Species.DOG,
        "breed": "Pitbull Mix",
        "age": "3 anos",
        "description": "Necesita cirugia urgente en pata trasera. Docil y amigable a pesar del dolor.",
        "medical_needs": "Cirugia pendiente en pata trasera, analgesicos diarios",
        "urgency": UrgencyLevel.CRITICAL,
        "status": AnimalStatus.IN_TREATMENT,
        "photo_urls": ["/images/animals/thor1.jpg"],
        "created_at": "2026-03-10T15:00:00Z",
        "updated_at": "2026-03-27T10:00:00Z",
        "adoption_story": None,
    },
    {
        "id": "ranim-005",
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": "Simba",
        "species": Species.CAT,
        "breed": "Naranja Comun",
        "age": "5 anos",
        "description": "Simba encontro su hogar definitivo con una familia amorosa.",
        "medical_needs": "",
        "urgency": UrgencyLevel.LOW,
        "status": AnimalStatus.ADOPTED,
        "photo_urls": ["/images/animals/simba1.jpg"],
        "created_at": "2025-09-15T09:00:00Z",
        "updated_at": "2026-02-28T16:00:00Z",
        "adoption_story": {
            "story_text": "Simba fue adoptado por la familia Rodriguez. Ahora vive feliz con dos niños que lo adoran.",
            "photo_url": "/images/stories/simba_happy.jpg",
            "adopter_name": "Familia Rodriguez",
        },
    },
    {
        "id": "ranim-006",
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": "Estrella",
        "species": Species.DOG,
        "breed": "Mestizo pequeno",
        "age": "6 meses",
        "description": "Cachorra encontrada abandonada. Necesita vacunacion completa y esterilizacion.",
        "medical_needs": "Vacunacion incompleta, desparasitacion pendiente",
        "urgency": UrgencyLevel.HIGH,
        "status": AnimalStatus.AVAILABLE,
        "photo_urls": ["/images/animals/estrella1.jpg", "/images/animals/estrella2.jpg"],
        "created_at": "2026-03-20T11:00:00Z",
        "updated_at": "2026-03-27T08:00:00Z",
        "adoption_story": None,
    },
]

# Rescuer slug mapping for public endpoint
RESCUER_SLUGS: dict[str, str] = {
    "carlos-mendoza": "Carlos Mendoza",
    "laura-gimenez": "Laura Gimenez",
}


def _init_store() -> None:
    """Initialize store with sample data."""
    _animals.clear()
    for animal in SAMPLE_ANIMALS:
        _animals[animal["id"]] = dict(animal)


def _reset_store() -> None:
    """Reset store to initial state (for testing)."""
    _init_store()


# Initialize on import
_init_store()


def _find_animal(animal_id: str) -> dict[str, Any]:
    """Find animal or raise 404."""
    animal = _animals.get(animal_id)
    if animal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Animal '{animal_id}' not found",
        )
    return animal


# ---------------------------------------------------------------------------
# Portal endpoints (rescuer-facing)
# ---------------------------------------------------------------------------


@portal_router.get("", response_model=AnimalListResponse)
async def list_my_animals(
    status_filter: AnimalStatus | None = None,
    species_filter: Species | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> AnimalListResponse:
    """List rescuer's animals."""
    rescuer_id = "resc-001"  # Simulated auth
    animals = [a for a in _animals.values() if a["rescuer_id"] == rescuer_id]

    if status_filter:
        animals = [a for a in animals if a["status"] == status_filter]
    if species_filter:
        animals = [a for a in animals if a["species"] == species_filter]

    # Sort by urgency, then date
    animals.sort(key=lambda a: (URGENCY_ORDER.get(a["urgency"], 99), a["created_at"]))

    total = len(animals)
    start = (page - 1) * page_size
    page_items = animals[start : start + page_size]

    return AnimalListResponse(
        animals=[RescuerAnimal(**a) for a in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@portal_router.post("", response_model=RescuerAnimal, status_code=status.HTTP_201_CREATED)
async def add_animal(request: AnimalCreateRequest) -> RescuerAnimal:
    """Add a new animal."""
    if len(request.photo_urls) > MAX_PHOTOS_PER_ANIMAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_PHOTOS_PER_ANIMAL} photos allowed",
        )

    now = datetime.now(UTC).isoformat()
    animal_id = f"ranim-{uuid4().hex[:8]}"

    animal: dict[str, Any] = {
        "id": animal_id,
        "rescuer_id": "resc-001",
        "rescuer_slug": "carlos-mendoza",
        "name": request.name,
        "species": request.species,
        "breed": request.breed,
        "age": request.age,
        "description": request.description,
        "medical_needs": request.medical_needs,
        "urgency": request.urgency,
        "status": AnimalStatus.AVAILABLE,
        "photo_urls": request.photo_urls,
        "created_at": now,
        "updated_at": now,
        "adoption_story": None,
    }
    _animals[animal_id] = animal

    logger.info("Animal added", extra={"animal_id": animal_id, "name": request.name})
    return RescuerAnimal(**animal)


@portal_router.get("/{animal_id}", response_model=RescuerAnimal)
async def get_animal(animal_id: str) -> RescuerAnimal:
    """Get animal details."""
    animal = _find_animal(animal_id)
    return RescuerAnimal(**animal)


@portal_router.put("/{animal_id}", response_model=RescuerAnimal)
async def update_animal(animal_id: str, request: AnimalUpdateRequest) -> RescuerAnimal:
    """Update animal details."""
    animal = _find_animal(animal_id)

    if request.photo_urls and len(request.photo_urls) > MAX_PHOTOS_PER_ANIMAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_PHOTOS_PER_ANIMAL} photos allowed",
        )

    update_data = request.model_dump(exclude_none=True)
    animal.update(update_data)
    animal["updated_at"] = datetime.now(UTC).isoformat()

    logger.info("Animal updated", extra={"animal_id": animal_id})
    return RescuerAnimal(**animal)


@portal_router.patch("/{animal_id}/status", response_model=AnimalActionResponse)
async def change_status(animal_id: str, request: StatusChangeRequest) -> AnimalActionResponse:
    """Change animal status with validation."""
    animal = _find_animal(animal_id)
    current = animal["status"]
    new = request.new_status

    valid = VALID_TRANSITIONS.get(current, [])
    if new not in valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{current}' to '{new}'. Valid: {valid}",
        )

    animal["status"] = new
    animal["updated_at"] = datetime.now(UTC).isoformat()

    logger.info(
        "Animal status changed",
        extra={"animal_id": animal_id, "from": current, "to": new},
    )

    return AnimalActionResponse(
        success=True,
        message=f"Status changed from '{current}' to '{new}'",
        animal_id=animal_id,
    )


@portal_router.delete("/{animal_id}", response_model=AnimalActionResponse)
async def delete_animal(animal_id: str) -> AnimalActionResponse:
    """Soft-delete (archive) an animal."""
    animal = _find_animal(animal_id)
    animal["status"] = AnimalStatus.ARCHIVED
    animal["updated_at"] = datetime.now(UTC).isoformat()

    logger.info("Animal archived", extra={"animal_id": animal_id})

    return AnimalActionResponse(
        success=True,
        message=f"Animal '{animal['name']}' archived",
        animal_id=animal_id,
    )


@portal_router.post("/{animal_id}/story", response_model=AnimalActionResponse)
async def add_adoption_story(animal_id: str, request: AdoptionStoryRequest) -> AnimalActionResponse:
    """Add an adoption story to an adopted animal."""
    animal = _find_animal(animal_id)

    if animal["status"] != AnimalStatus.ADOPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adoption stories can only be added to adopted animals",
        )

    animal["adoption_story"] = {
        "story_text": request.story_text,
        "photo_url": request.photo_url,
        "adopter_name": request.adopter_name,
    }
    animal["updated_at"] = datetime.now(UTC).isoformat()

    logger.info("Adoption story added", extra={"animal_id": animal_id})

    return AnimalActionResponse(
        success=True,
        message="Adoption story added",
        animal_id=animal_id,
    )


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@public_router.get("/{slug}/animals", response_model=PublicAnimalListResponse)
async def list_public_animals(
    slug: str,
    species: Species | None = None,
    urgency: UrgencyLevel | None = None,
) -> PublicAnimalListResponse:
    """Public listing of available animals for a rescuer."""
    rescuer_name = RESCUER_SLUGS.get(slug)
    if rescuer_name is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rescuer '{slug}' not found",
        )

    animals = [
        a
        for a in _animals.values()
        if a.get("rescuer_slug") == slug and a["status"] == AnimalStatus.AVAILABLE
    ]

    if species:
        animals = [a for a in animals if a["species"] == species]
    if urgency:
        animals = [a for a in animals if a["urgency"] == urgency]

    # Sort critical/high first
    animals.sort(key=lambda a: URGENCY_ORDER.get(a["urgency"], 99))

    cards = [
        PublicAnimalCard(
            id=a["id"],
            name=a["name"],
            species=a["species"],
            species_label=SPECIES_LABELS_ES.get(a["species"], a["species"]),
            breed=a["breed"],
            age=a["age"],
            description=a["description"],
            medical_needs=a["medical_needs"],
            urgency=a["urgency"],
            urgency_label=URGENCY_LABELS_ES.get(a["urgency"], a["urgency"]),
            photo_url=a["photo_urls"][0] if a["photo_urls"] else None,
            rescue_date=a["created_at"][:10],
        )
        for a in animals
    ]

    return PublicAnimalListResponse(
        animals=cards,
        total=len(cards),
        rescuer_name=rescuer_name,
    )
