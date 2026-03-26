"""Unit tests for src/schemas/public.py — public browsing response schemas."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.animal import AnimalGender, AnimalSize, AnimalSpecies
from src.schemas.public import (
    PaginatedAnimalResponse,
    PaginationMeta,
    PublicAnimalDetail,
    PublicAnimalListItem,
    PublicPhotoResponse,
)


class TestPublicPhotoResponse:
    def test_valid_photo(self) -> None:
        photo = PublicPhotoResponse(
            id=uuid4(),
            url="https://example.com/photo.jpg",
            caption="A cute dog",
            display_order=0,
        )
        assert photo.url == "https://example.com/photo.jpg"
        assert photo.caption == "A cute dog"

    def test_nullable_caption(self) -> None:
        photo = PublicPhotoResponse(
            id=uuid4(),
            url="https://example.com/photo.jpg",
            caption=None,
            display_order=0,
        )
        assert photo.caption is None


class TestPublicAnimalListItem:
    def test_complete_item(self) -> None:
        item = PublicAnimalListItem(
            id=uuid4(),
            name="Firulais",
            species=AnimalSpecies.DOG,
            breed="Labrador",
            size=AnimalSize.LARGE,
            gender=AnimalGender.MALE,
            birth_date=date(2023, 1, 15),
            description="Friendly dog",
            primary_photo_url="https://example.com/photo.jpg",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert item.name == "Firulais"
        assert item.species == AnimalSpecies.DOG
        assert item.breed == "Labrador"
        assert item.size == AnimalSize.LARGE
        assert item.gender == AnimalGender.MALE

    def test_nullable_fields_explicit_null(self) -> None:
        """Nullable fields are represented as null, never omitted."""
        item = PublicAnimalListItem(
            id=uuid4(),
            name="Unknown",
            species=AnimalSpecies.OTHER,
            breed=None,
            size=None,
            gender=None,
            birth_date=None,
            description=None,
            primary_photo_url=None,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        data = item.model_dump()
        assert data["breed"] is None
        assert data["size"] is None
        assert data["gender"] is None
        assert data["birth_date"] is None
        assert data["description"] is None
        assert data["primary_photo_url"] is None


class TestPublicAnimalDetail:
    def test_includes_photos_list(self) -> None:
        photo = PublicPhotoResponse(
            id=uuid4(),
            url="https://example.com/photo.jpg",
            caption=None,
            display_order=0,
        )
        detail = PublicAnimalDetail(
            id=uuid4(),
            name="Luna",
            species=AnimalSpecies.CAT,
            breed="Siamese",
            size=AnimalSize.SMALL,
            gender=AnimalGender.FEMALE,
            birth_date=date(2024, 6, 1),
            description="Playful cat",
            primary_photo_url="https://example.com/photo.jpg",
            photos=[photo],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
        assert len(detail.photos) == 1
        assert detail.photos[0].url == "https://example.com/photo.jpg"

    def test_empty_photos_returns_empty_list(self) -> None:
        detail = PublicAnimalDetail(
            id=uuid4(),
            name="Rex",
            species=AnimalSpecies.DOG,
            breed=None,
            size=None,
            gender=None,
            birth_date=None,
            description=None,
            primary_photo_url=None,
            photos=[],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert detail.photos == []
        # Ensure it serializes as empty array, not null
        data = detail.model_dump()
        assert data["photos"] == []


class TestPaginationMeta:
    def test_valid_pagination(self) -> None:
        meta = PaginationMeta(
            page=1,
            page_size=20,
            total_items=45,
            total_pages=3,
        )
        assert meta.page == 1
        assert meta.total_pages == 3

    def test_page_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            PaginationMeta(page=0, page_size=20, total_items=0, total_pages=0)

    def test_empty_results(self) -> None:
        meta = PaginationMeta(
            page=1,
            page_size=20,
            total_items=0,
            total_pages=0,
        )
        assert meta.total_items == 0
        assert meta.total_pages == 0


class TestPaginatedAnimalResponse:
    def test_empty_response(self) -> None:
        response = PaginatedAnimalResponse(
            items=[],
            pagination=PaginationMeta(page=1, page_size=20, total_items=0, total_pages=0),
        )
        assert response.items == []
        assert response.pagination.total_items == 0

    def test_response_with_items(self) -> None:
        item = PublicAnimalListItem(
            id=uuid4(),
            name="Buddy",
            species=AnimalSpecies.DOG,
            breed="Mixed",
            size=AnimalSize.MEDIUM,
            gender=AnimalGender.MALE,
            birth_date=date(2022, 3, 1),
            description="Good boy",
            primary_photo_url=None,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        response = PaginatedAnimalResponse(
            items=[item],
            pagination=PaginationMeta(page=1, page_size=20, total_items=1, total_pages=1),
        )
        assert len(response.items) == 1
        assert response.items[0].name == "Buddy"
