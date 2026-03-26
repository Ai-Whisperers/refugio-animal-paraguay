"""Unit tests for InKindDonation model and ItemType enum."""

from uuid import uuid4

from src.db.models.in_kind_donation import InKindDonation, ItemType


class TestItemType:
    """Tests for the ItemType enum."""

    def test_item_type_is_string_enum(self) -> None:
        assert isinstance(ItemType.FOOD, str)
        assert ItemType.FOOD == "food"

    def test_all_expected_types_exist(self) -> None:
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
        actual = {t.value for t in ItemType}
        assert actual == expected

    def test_item_type_count(self) -> None:
        assert len(ItemType) == 9


class TestInKindDonationModel:
    """Tests for the InKindDonation ORM model."""

    def test_tablename(self) -> None:
        assert InKindDonation.__tablename__ == "in_kind_donations"

    def test_instantiate_with_required_fields(self) -> None:
        donation = InKindDonation(
            item_type=ItemType.FOOD.value,
            description="50kg bag of dog food",
            estimated_value_cents=150000,
        )
        assert donation.item_type == "food"
        assert donation.description == "50kg bag of dog food"
        assert donation.estimated_value_cents == 150000

    def test_optional_fields_default_to_none(self) -> None:
        donation = InKindDonation(
            item_type=ItemType.SUPPLIES.value,
            description="Cleaning supplies",
            estimated_value_cents=50000,
        )
        assert donation.donor_id is None
        assert donation.received_by_user_id is None
        assert donation.notes is None

    def test_optional_fields_accept_values(self) -> None:
        donor_id = uuid4()
        user_id = uuid4()
        donation = InKindDonation(
            donor_id=donor_id,
            item_type=ItemType.VETERINARY_SERVICES.value,
            description="Free spay/neuter surgery",
            quantity=3,
            estimated_value_cents=900000,
            currency="PYG",
            received_by_user_id=user_id,
            notes="Dr. Rodriguez donation",
        )
        assert donation.donor_id == donor_id
        assert donation.quantity == 3
        assert donation.received_by_user_id == user_id
        assert donation.notes == "Dr. Rodriguez donation"

    def test_table_has_expected_indexes(self) -> None:
        index_names = {idx.name for idx in InKindDonation.__table__.indexes}
        assert "ix_in_kind_donations_donor_id_date" in index_names
        assert "ix_in_kind_donations_item_type" in index_names
