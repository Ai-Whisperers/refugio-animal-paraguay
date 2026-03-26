"""Animals CRUD router.

Endpoints:
  GET    /animals                          — paginated list, filterable by species/status
  GET    /animals/{id}                     — single animal or 404
  POST   /animals                          — create, returns 201
  PATCH  /animals/{id}                     — partial update, returns 200 or 404
  DELETE /animals/{id}                     — hard delete, returns 204 or 404
  POST   /animals/{id}/photos              — add gallery photo, returns 201 (staff only)
  DELETE /animals/{id}/photos/{photo_id}   — remove gallery photo, returns 204 (staff only)
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_staff
from src.db.models.animal import (
    Animal,
    AnimalGender,
    AnimalPhoto,
    AnimalSize,
    AnimalSpecies,
    AnimalStatus,
)
from src.db.models.user import User
from src.db.session import get_db
from src.schemas.animal import (
    AnimalCreate,
    AnimalResponse,
    AnimalUpdate,
    PhotoCreate,
    PhotoResponse,
)

router = APIRouter(prefix="/animals", tags=["animals"])

_DEFAULT_LIMIT = 20
_MAX_LIMIT = 100


@router.get("", response_model=list[AnimalResponse])
async def list_animals(
    species: AnimalSpecies | None = Query(default=None),
    status: AnimalStatus | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    db: AsyncSession = Depends(get_db),
) -> list[Animal]:
    stmt = select(Animal)
    if species is not None:
        stmt = stmt.where(Animal.species == species.value)
    if status is not None:
        stmt = stmt.where(Animal.status == status.value)
    stmt = stmt.offset(offset).limit(limit).order_by(Animal.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{animal_id}", response_model=AnimalResponse)
async def get_animal(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Animal:
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    return animal


@router.post("", response_model=AnimalResponse, status_code=status.HTTP_201_CREATED)
async def create_animal(
    payload: AnimalCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Animal:
    animal = Animal(
        name=payload.name,
        species=payload.species.value,
        status=payload.status.value,
        breed=payload.breed,
        size=payload.size.value if payload.size else None,
        gender=payload.gender.value if payload.gender else None,
        birth_date=payload.birth_date,
        description=payload.description,
        primary_photo_url=payload.primary_photo_url,
    )
    db.add(animal)
    await db.flush()
    await db.refresh(animal)
    return animal


@router.patch("/{animal_id}", response_model=AnimalResponse)
async def update_animal(
    animal_id: UUID,
    payload: AnimalUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Animal:
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        # Enum fields stored as plain strings in DB
        if isinstance(value, (AnimalSpecies, AnimalStatus, AnimalSize, AnimalGender)):
            value = value.value
        setattr(animal, field, value)

    # Explicitly set updated_at — onupdate fires on flush but we want it visible after refresh
    animal.updated_at = datetime.now(UTC)

    await db.flush()
    await db.refresh(animal)
    return animal


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_animal(
    animal_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Response:
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    await db.delete(animal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{animal_id}/photos",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_animal_photo(
    animal_id: UUID,
    payload: PhotoCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> AnimalPhoto:
    animal = await db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animal not found")
    photo = AnimalPhoto(
        animal_id=animal_id,
        url=payload.url,
        caption=payload.caption,
        display_order=payload.display_order,
    )
    db.add(photo)
    await db.flush()
    await db.refresh(photo)
    return photo


@router.delete(
    "/{animal_id}/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_animal_photo(
    animal_id: UUID,
    photo_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
) -> Response:
    stmt = select(AnimalPhoto).where(
        AnimalPhoto.id == photo_id,
        AnimalPhoto.animal_id == animal_id,
    )
    result = await db.execute(stmt)
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    await db.delete(photo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
