"""Unit tests for in-kind donation Pydantic schemas."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.db.models.donation import CurrencyCode
from src.db.models.in_kind_donation import ItemType
from src.schemas.in_kind_donation import (
    InKindDonationCreate,
    InKindDonationListResponse,
    InKindDonationResponse,
)


class TestInKindDonationCreate:
    """Tests for the in-kind donation creation schema."""

    def test_minimal_valid_payload(self) -> None:
        schema = InKindDonationCreate(
            item_type=ItemType.FOOD,
            description="Bag of dog food",
            estimated_value_cents=50000,
        )
        assert schema.item_type == ItemType.FOOD
        assert schema.quantity == 1
        assert schema.currency == CurrencyCode.PYG
        assert schema.donor_id is None
        assert schema.date_received is None
        assert schema.notes is None

    def test_full_payload(self) -> None:
        donor_id = uuid4()
        now = datetime.now(UTC)
        schema = InKindDonationCreate(
            donor_id=donor_id,
            item_type=ItemType.MEDICATION,
            description="Antiparasitic medication x20 doses",
            quantity=20,
            estimated_value_cents=300000,
            currency=CurrencyCode.PYG,
            date_received=now,
            notes="Donated by local pharmacy",
        )
        assert schema.donor_id == donor_id
        assert schema.quantity == 20
        assert schema.estimated_value_cents == 300000
        assert schema.notes == "Donated by local pharmacy"

    def test_default_currency_is_pyg(self) -> None:
        schema = InKindDonationCreate(
            item_type=ItemType.TOYS,
            description="Dog toys",
            estimated_value_cents=10000,
        )
        assert schema.currency == CurrencyCode.PYG

    def test_supports_eur_currency(self) -> None:
        schema = InKindDonationCreate(
            item_type=ItemType.EQUIPMENT,
            description="Dog crate",
            estimated_value_cents=5000,
            currency=CurrencyCode.EUR,
        )
        assert schema.currency == CurrencyCode.EUR

    def test_estimated_value_must_be_positive(self) -> None:
        with pytest.raises(ValidationError):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                description="Dog food",
                estimated_value_cents=0,
            )

    def test_negative_value_rejected(self) -> None:
        with pytest.raises(ValidationError):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                description="Dog food",
                estimated_value_cents=-100,
            )

    def test_quantity_must_be_at_least_one(self) -> None:
        with pytest.raises(ValidationError):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                description="Dog food",
                estimated_value_cents=1000,
                quantity=0,
            )

    def test_description_required(self) -> None:
        with pytest.raises(ValidationError):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                description="",
                estimated_value_cents=1000,
            )

    def test_description_max_length(self) -> None:
        with pytest.raises(ValidationError):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                description="X" * 501,
                estimated_value_cents=1000,
            )

    def test_all_item_types_accepted(self) -> None:
        for item_type in ItemType:
            schema = InKindDonationCreate(
                item_type=item_type,
                description=f"Test {item_type.value}",
                estimated_value_cents=1000,
            )
            assert schema.item_type == item_type


class TestInKindDonationResponse:
    """Tests for the in-kind donation response schema."""

    def test_serialization_roundtrip(self) -> None:
        now = datetime.now(UTC)
        resp = InKindDonationResponse(
            id=uuid4(),
            donor_id=None,
            item_type=ItemType.BEDDING,
            description="Dog beds x5",
            quantity=5,
            estimated_value_cents=250000,
            currency=CurrencyCode.PYG,
            date_received=now,
            received_by_user_id=uuid4(),
            notes=None,
            created_at=now,
            updated_at=now,
        )
        data = resp.model_dump(mode="json")
        restored = InKindDonationResponse.model_validate(data)
        assert restored.item_type == ItemType.BEDDING
        assert restored.quantity == 5


class TestInKindDonationListResponse:
    """Tests for the paginated list response."""

    def test_empty_list(self) -> None:
        resp = InKindDonationListResponse(items=[], total=0, page=1, page_size=20)
        assert resp.items == []
        assert resp.total == 0

    def test_with_items(self) -> None:
        now = datetime.now(UTC)
        item = InKindDonationResponse(
            id=uuid4(),
            donor_id=None,
            item_type=ItemType.FOOD,
            description="Cat food",
            quantity=10,
            estimated_value_cents=100000,
            currency=CurrencyCode.PYG,
            date_received=now,
            received_by_user_id=None,
            notes=None,
            created_at=now,
            updated_at=now,
        )
        resp = InKindDonationListResponse(items=[item], total=1, page=1, page_size=20)
        assert len(resp.items) == 1
