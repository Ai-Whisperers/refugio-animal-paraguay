"""Unit tests for public animal browsing Pydantic schemas."""

from datetime import datetime, timezone
from uuid import uuid4

from src.schemas.public_animal import (
    PaginatedResponse,
    PublicAnimalDetail,
    PublicAnimalSummary,
    PublicPhotoResponse,
)


class TestPublicPhotoResponse:
    def test_from_orm_attributes(self) -> None:
        uid = uuid4()

        class _FakePhoto:
            id = uid
            url = "https://cdn.example.com/photo.jpg"
            caption = "A friendly dog"
            display_order = 0

        resp = PublicPhotoResponse.model_validate(_FakePhoto())
        assert resp.id == uid
        assert resp.url == "https://cdn.example.com/photo.jpg"
        assert resp.caption == "A friendly dog"
        assert resp.display_order == 0

    def test_nullable_caption(self) -> None:
        uid = uuid4()

        class _FakePhoto:
            id = uid
            url = "https://cdn.example.com/photo.jpg"
            caption = None
            display_order = 1

        resp = PublicPhotoResponse.model_validate(_FakePhoto())
        assert resp.caption is None


class TestPublicAnimalSummary:
    def test_from_orm_attributes(self) -> None:
        uid = uuid4()
        now = datetime.now(timezone.utc)

        class _FakeAnimal:
            id = uid
            name = "Luna"
            species = "dog"
            gender = "female"
            size = "medium"
            birth_date = None
            description = "Friendly dog"
            primary_photo_url = "https://cdn.example.com/luna.jpg"
            created_at = now

        resp = PublicAnimalSummary.model_validate(_FakeAnimal())
        assert resp.id == uid
        assert resp.name == "Luna"
        assert resp.species.value == "dog"
        assert resp.gender is not None
        assert resp.gender.value == "female"
        assert resp.size is not None
        assert resp.size.value == "medium"

    def test_nullable_optional_fields(self) -> None:
        uid = uuid4()
        now = datetime.now(timezone.utc)

        class _FakeAnimal:
            id = uid
            name = "Max"
            species = "cat"
            gender = None
            size = None
            birth_date = None
            description = None
            primary_photo_url = None
            created_at = now

        resp = PublicAnimalSummary.model_validate(_FakeAnimal())
        assert resp.gender is None
        assert resp.size is None
        assert resp.description is None
        assert resp.primary_photo_url is None


class TestPublicAnimalDetail:
    def test_includes_photos(self) -> None:
        uid = uuid4()
        photo_id = uuid4()
        now = datetime.now(timezone.utc)

        class _FakePhoto:
            id = photo_id
            url = "https://cdn.example.com/photo.jpg"
            caption = None
            display_order = 0

        class _FakeAnimal:
            id = uid
            name = "Bolt"
            species = "dog"
            gender = "male"
            size = "large"
            birth_date = None
            description = "Fast runner"
            primary_photo_url = "https://cdn.example.com/bolt.jpg"
            photos = [_FakePhoto()]
            created_at = now
            updated_at = now

        resp = PublicAnimalDetail.model_validate(_FakeAnimal())
        assert resp.id == uid
        assert len(resp.photos) == 1
        assert resp.photos[0].id == photo_id

    def test_empty_photos_list(self) -> None:
        uid = uuid4()
        now = datetime.now(timezone.utc)

        class _FakeAnimal:
            id = uid
            name = "Solo"
            species = "cat"
            gender = None
            size = None
            birth_date = None
            description = None
            primary_photo_url = None
            photos: list = []
            created_at = now
            updated_at = now

        resp = PublicAnimalDetail.model_validate(_FakeAnimal())
        assert resp.photos == []


class TestPaginatedResponse:
    def test_structure(self) -> None:
        resp = PaginatedResponse[PublicAnimalSummary](
            items=[],
            total=0,
            page=1,
            size=20,
            pages=1,
        )
        assert resp.items == []
        assert resp.total == 0
        assert resp.page == 1
        assert resp.size == 20
        assert resp.pages == 1

    def test_with_items(self) -> None:
        uid = uuid4()
        now = datetime.now(timezone.utc)
        summary = PublicAnimalSummary(
            id=uid,
            name="Test",
            species="dog",
            gender=None,
            size=None,
            birth_date=None,
            description=None,
            primary_photo_url=None,
            created_at=now,
        )
        resp = PaginatedResponse[PublicAnimalSummary](
            items=[summary],
            total=1,
            page=1,
            size=20,
            pages=1,
        )
        assert len(resp.items) == 1
        assert resp.items[0].name == "Test"
