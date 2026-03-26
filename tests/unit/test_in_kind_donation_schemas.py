"""Unit tests for in-kind donation schemas and model enums."""

from datetime import UTC

import pytest
from pydantic import ValidationError
from src.db.models.donation import CurrencyCode, ItemType
from src.schemas.in_kind_donation import (
    DonorGivingSummary,
    InKindDonationCreate,
    InKindDonationListResponse,
    InKindDonationResponse,
    InKindDonationUpdate,
)

# ---------------------------------------------------------------------------
# ItemType enum
# ---------------------------------------------------------------------------


class TestItemType:
    def test_all_item_types_defined(self) -> None:
        expected = {
            "food",
            "medication",
            "equipment",
            "toys",
            "bedding",
            "supplies",
            "veterinary_services",
            "transportation",
            "other",
        }
        actual = {item.value for item in ItemType}
        assert actual == expected

    def test_item_type_count(self) -> None:
        assert len(ItemType) == 9

    def test_item_type_is_string(self) -> None:
        assert ItemType.FOOD == "food"
        assert ItemType.VETERINARY_SERVICES == "veterinary_services"


# ---------------------------------------------------------------------------
# InKindDonationCreate
# ---------------------------------------------------------------------------


class TestInKindDonationCreate:
    def test_minimal_valid_creation(self) -> None:
        schema = InKindDonationCreate(
            item_type=ItemType.FOOD,
            estimated_value_cents=2500,
        )
        assert schema.item_type == ItemType.FOOD
        assert schema.estimated_value_cents == 2500
        assert schema.quantity == 1
        assert schema.currency == CurrencyCode.EUR
        assert schema.donor_id is None
        assert schema.description is None
        assert schema.notes is None
        assert schema.date_received is None

    def test_full_creation(self) -> None:
        from datetime import datetime
        from uuid import uuid4

        donor_id = uuid4()
        now = datetime.now(tz=UTC)
        schema = InKindDonationCreate(
            donor_id=donor_id,
            item_type=ItemType.MEDICATION,
            description="Antiparasitic medication",
            quantity=10,
            estimated_value_cents=15000,
            currency=CurrencyCode.USD,
            date_received=now,
            notes="Monthly donation from vet clinic",
        )
        assert schema.donor_id == donor_id
        assert schema.quantity == 10
        assert schema.currency == CurrencyCode.USD
        assert schema.date_received == now

    def test_zero_estimated_value_is_valid(self) -> None:
        schema = InKindDonationCreate(
            item_type=ItemType.OTHER,
            estimated_value_cents=0,
        )
        assert schema.estimated_value_cents == 0

    def test_negative_estimated_value_rejected(self) -> None:
        with pytest.raises(ValidationError, match="estimated_value_cents"):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                estimated_value_cents=-100,
            )

    def test_zero_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError, match="quantity"):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                quantity=0,
                estimated_value_cents=1000,
            )

    def test_negative_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError, match="quantity"):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                quantity=-1,
                estimated_value_cents=1000,
            )

    def test_description_max_length(self) -> None:
        with pytest.raises(ValidationError, match="description"):
            InKindDonationCreate(
                item_type=ItemType.FOOD,
                description="x" * 501,
                estimated_value_cents=1000,
            )

    def test_missing_item_type_rejected(self) -> None:
        with pytest.raises(ValidationError, match="item_type"):
            InKindDonationCreate(estimated_value_cents=1000)  # type: ignore[call-arg]

    def test_missing_estimated_value_rejected(self) -> None:
        with pytest.raises(ValidationError, match="estimated_value_cents"):
            InKindDonationCreate(item_type=ItemType.FOOD)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# InKindDonationUpdate
# ---------------------------------------------------------------------------


class TestInKindDonationUpdate:
    def test_empty_update_valid(self) -> None:
        schema = InKindDonationUpdate()
        assert schema.model_dump(exclude_unset=True) == {}

    def test_partial_update(self) -> None:
        schema = InKindDonationUpdate(quantity=5, notes="Updated notes")
        dumped = schema.model_dump(exclude_unset=True)
        assert dumped == {"quantity": 5, "notes": "Updated notes"}

    def test_update_item_type(self) -> None:
        schema = InKindDonationUpdate(item_type=ItemType.BEDDING)
        assert schema.item_type == ItemType.BEDDING

    def test_update_negative_value_rejected(self) -> None:
        with pytest.raises(ValidationError, match="estimated_value_cents"):
            InKindDonationUpdate(estimated_value_cents=-50)


# ---------------------------------------------------------------------------
# InKindDonationResponse
# ---------------------------------------------------------------------------


class TestInKindDonationResponse:
    def test_from_attributes_config(self) -> None:
        assert InKindDonationResponse.model_config.get("from_attributes") is True


# ---------------------------------------------------------------------------
# InKindDonationListResponse
# ---------------------------------------------------------------------------


class TestInKindDonationListResponse:
    def test_empty_list(self) -> None:
        resp = InKindDonationListResponse(items=[], total=0, limit=20, offset=0)
        assert resp.items == []
        assert resp.total == 0


# ---------------------------------------------------------------------------
# DonorGivingSummary
# ---------------------------------------------------------------------------


class TestDonorGivingSummary:
    def test_giving_summary_fields(self) -> None:
        from uuid import uuid4

        donor_id = uuid4()
        summary = DonorGivingSummary(
            donor_id=donor_id,
            donor_name="Test Donor",
            cash_total_cents=10000,
            cash_donation_count=3,
            in_kind_total_cents=5000,
            in_kind_donation_count=2,
            combined_total_cents=15000,
            currency="EUR",
        )
        assert summary.combined_total_cents == 15000
        assert summary.cash_donation_count == 3
        assert summary.in_kind_donation_count == 2
