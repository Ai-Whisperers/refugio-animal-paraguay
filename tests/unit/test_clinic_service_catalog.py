"""Unit tests for the clinic service catalog service layer."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from src.db.models.clinic_service import ServiceCategory
from src.services.clinic_service_catalog import (
    ClinicNotFoundError,
    ClinicServiceNotFoundError,
    create_service,
    delete_service,
    get_service,
    update_service,
)


class TestCreateService:
    """Tests for creating a clinic service."""

    @pytest.mark.asyncio()
    async def test_creates_service_when_clinic_exists(self) -> None:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        # db.get returns the clinic (exists)
        db.get.return_value = MagicMock()

        clinic_id = uuid4()
        data = {
            "name": "Vacunacion antirabica",
            "category": ServiceCategory.VACCINATION,
            "price_pyg": 150000,
        }

        await create_service(db, clinic_id, data)
        assert db.add.called
        assert db.flush.called
        assert db.refresh.called

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_clinic_missing(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ClinicNotFoundError):
            await create_service(db, uuid4(), {"name": "X", "price_pyg": 0})


class TestGetService:
    """Tests for fetching a single service."""

    @pytest.mark.asyncio()
    async def test_returns_service_when_found(self) -> None:
        db = AsyncMock()
        # clinic exists
        db.get.return_value = MagicMock()
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_service
        db.execute.return_value = mock_result

        result = await get_service(db, uuid4(), uuid4())
        assert result == mock_service

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_service_missing(self) -> None:
        db = AsyncMock()
        # clinic exists
        db.get.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        service_id = uuid4()
        with pytest.raises(ClinicServiceNotFoundError, match=str(service_id)):
            await get_service(db, uuid4(), service_id)

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_clinic_missing(self) -> None:
        db = AsyncMock()
        db.get.return_value = None

        with pytest.raises(ClinicNotFoundError):
            await get_service(db, uuid4(), uuid4())


class TestUpdateService:
    """Tests for updating service fields."""

    @pytest.mark.asyncio()
    async def test_updates_provided_fields(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        # clinic exists
        db.get.return_value = MagicMock()

        mock_service = MagicMock()
        mock_service.name = "Old Name"
        mock_service.price_pyg = 100000
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_service
        db.execute.return_value = mock_result

        result = await update_service(
            db, uuid4(), uuid4(), {"name": "New Name", "price_pyg": 200000}
        )
        assert result.name == "New Name"
        assert result.price_pyg == 200000

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_service_missing(self) -> None:
        db = AsyncMock()
        db.get.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(ClinicServiceNotFoundError):
            await update_service(db, uuid4(), uuid4(), {"name": "X"})


class TestDeleteService:
    """Tests for deleting a service."""

    @pytest.mark.asyncio()
    async def test_deletes_existing_service(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        db.delete = AsyncMock()
        # clinic exists
        db.get.return_value = MagicMock()

        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_service
        db.execute.return_value = mock_result

        await delete_service(db, uuid4(), uuid4())
        assert db.delete.called

    @pytest.mark.asyncio()
    async def test_raises_not_found_when_service_missing(self) -> None:
        db = AsyncMock()
        db.get.return_value = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(ClinicServiceNotFoundError):
            await delete_service(db, uuid4(), uuid4())


class TestSchemaValidation:
    """Tests for clinic service schemas."""

    def test_service_category_enum_values(self) -> None:
        assert ServiceCategory.CONSULTATION == "consultation"
        assert ServiceCategory.VACCINATION == "vaccination"
        assert ServiceCategory.SURGERY == "surgery"
        assert ServiceCategory.DENTAL == "dental"
        assert ServiceCategory.DIAGNOSTIC == "diagnostic"
        assert ServiceCategory.GROOMING == "grooming"
        assert ServiceCategory.EMERGENCY == "emergency"
        assert ServiceCategory.PREVENTIVE == "preventive"
        assert ServiceCategory.OTHER == "other"

    def test_clinic_service_create_schema_validation(self) -> None:
        from src.schemas.clinic_service import ClinicServiceCreate

        service = ClinicServiceCreate(
            name="Consulta general",
            category="consultation",
            price_pyg=100000,
            price_eur=15.00,
            duration_minutes=30,
        )
        assert service.name == "Consulta general"
        assert service.price_pyg == 100000
        assert service.price_eur == 15.00
        assert service.duration_minutes == 30
        assert service.is_active is True

    def test_clinic_service_create_rejects_negative_price(self) -> None:
        from pydantic import ValidationError
        from src.schemas.clinic_service import ClinicServiceCreate

        with pytest.raises(ValidationError, match="price_pyg"):
            ClinicServiceCreate(
                name="Test",
                category="other",
                price_pyg=-1,
            )

    def test_clinic_service_create_rejects_zero_duration(self) -> None:
        from pydantic import ValidationError
        from src.schemas.clinic_service import ClinicServiceCreate

        with pytest.raises(ValidationError, match="duration_minutes"):
            ClinicServiceCreate(
                name="Test",
                category="other",
                price_pyg=1000,
                duration_minutes=0,
            )

    def test_clinic_service_create_defaults(self) -> None:
        from src.schemas.clinic_service import ClinicServiceCreate

        service = ClinicServiceCreate(name="Basic", price_pyg=50000)
        assert service.category == "other"
        assert service.is_active is True
        assert service.description is None
        assert service.price_eur is None
        assert service.duration_minutes is None

    def test_clinic_service_update_all_optional(self) -> None:
        from src.schemas.clinic_service import ClinicServiceUpdate

        update = ClinicServiceUpdate()
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {}

    def test_clinic_service_response_from_attributes(self) -> None:
        from datetime import UTC, datetime

        from src.schemas.clinic_service import ClinicServiceResponse

        now = datetime.now(UTC)
        service_id = uuid4()
        clinic_id = uuid4()

        response = ClinicServiceResponse.model_validate(
            {
                "id": service_id,
                "clinic_id": clinic_id,
                "name": "Cirugia",
                "description": "Cirugia general",
                "category": "surgery",
                "price_pyg": 500000,
                "price_eur": 70.00,
                "duration_minutes": 120,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        )
        assert response.id == service_id
        assert response.clinic_id == clinic_id
        assert response.price_pyg == 500000


class TestExceptionMessages:
    """Tests for exception attributes."""

    def test_clinic_service_not_found_has_id(self) -> None:
        service_id = uuid4()
        err = ClinicServiceNotFoundError(service_id)
        assert err.service_id == service_id
        assert str(service_id) in err.message

    def test_clinic_not_found_has_id(self) -> None:
        clinic_id = uuid4()
        err = ClinicNotFoundError(clinic_id)
        assert err.clinic_id == clinic_id
        assert str(clinic_id) in err.message
