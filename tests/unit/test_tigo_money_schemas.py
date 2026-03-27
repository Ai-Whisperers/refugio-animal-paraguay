"""Unit tests for Tigo Money Pydantic schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.schemas.tigo_money import TigoCallbackRequest, TigoPaymentInitRequest


class TestTigoPaymentInitRequest:
    def test_valid_request(self) -> None:
        req = TigoPaymentInitRequest(
            donor_id=uuid4(),
            amount_pyg=50000,
            return_url="https://example.com/return",
        )
        assert req.amount_pyg == 50000
        assert req.fund_category == "general"
        assert req.campaign_id is None

    def test_zero_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TigoPaymentInitRequest(
                donor_id=uuid4(),
                amount_pyg=0,
                return_url="https://example.com/return",
            )

    def test_negative_amount_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TigoPaymentInitRequest(
                donor_id=uuid4(),
                amount_pyg=-1000,
                return_url="https://example.com/return",
            )

    def test_with_campaign_id(self) -> None:
        campaign_id = uuid4()
        req = TigoPaymentInitRequest(
            donor_id=uuid4(),
            amount_pyg=100000,
            return_url="https://example.com/return",
            campaign_id=campaign_id,
        )
        assert req.campaign_id == campaign_id


class TestTigoCallbackRequest:
    def test_valid_completed_callback(self) -> None:
        cb = TigoCallbackRequest(
            transactionId="TXN-001",
            reference="ref-001",
            status="COMPLETED",
            amount="200000",
        )
        assert cb.status == "COMPLETED"

    def test_status_is_uppercased(self) -> None:
        cb = TigoCallbackRequest(
            transactionId="TXN-002",
            reference="ref-002",
            status="completed",
            amount="100000",
        )
        assert cb.status == "COMPLETED"

    def test_unknown_status_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TigoCallbackRequest(
                transactionId="TXN-003",
                reference="ref-003",
                status="UNKNOWN_STATUS",
                amount="100000",
            )

    def test_failed_status_accepted(self) -> None:
        cb = TigoCallbackRequest(
            transactionId="TXN-004",
            reference="ref-004",
            status="FAILED",
            amount="50000",
        )
        assert cb.status == "FAILED"

    def test_cancelled_status_accepted(self) -> None:
        cb = TigoCallbackRequest(
            transactionId="TXN-005",
            reference="ref-005",
            status="cancelled",
            amount="50000",
        )
        assert cb.status == "CANCELLED"
