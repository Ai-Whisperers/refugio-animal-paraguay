"""Unit tests for the donor tax ID secure storage service."""

import pytest
from cryptography.fernet import Fernet
from src.services.donor_tax_id_service import (
    BSN_MAX_LENGTH,
    BSN_MIN_LENGTH,
    DonorTaxIDService,
    TaxIDDecryptionError,
    TaxIDEncryptionKeyNotConfiguredError,
    TaxIDValidationError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fernet_key() -> str:
    """Generate a fresh Fernet key for each test."""
    return Fernet.generate_key().decode()


@pytest.fixture
def service(fernet_key: str) -> DonorTaxIDService:
    """Return a DonorTaxIDService with a fresh key."""
    return DonorTaxIDService(fernet_key)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_valid_key_succeeds(self, fernet_key: str) -> None:
        svc = DonorTaxIDService(fernet_key)
        assert svc is not None

    def test_empty_key_raises(self) -> None:
        with pytest.raises(TaxIDEncryptionKeyNotConfiguredError):
            DonorTaxIDService("")

    def test_none_key_raises(self) -> None:
        with pytest.raises((TaxIDEncryptionKeyNotConfiguredError, Exception)):
            DonorTaxIDService(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# encrypt / decrypt round-trip
# ---------------------------------------------------------------------------


class TestEncryptDecrypt:
    def test_encrypt_returns_string(self, service: DonorTaxIDService) -> None:
        result = service.encrypt("123456789")
        assert isinstance(result, str)

    def test_encrypt_does_not_return_plaintext(self, service: DonorTaxIDService) -> None:
        tax_id = "123456789"
        encrypted = service.encrypt(tax_id)
        assert tax_id not in encrypted

    def test_decrypt_recovers_plaintext(self, service: DonorTaxIDService) -> None:
        tax_id = "123456789"
        encrypted = service.encrypt(tax_id)
        assert service.decrypt(encrypted) == tax_id

    def test_round_trip_various_formats(self, service: DonorTaxIDService) -> None:
        for tax_id in ["12345678", "123456789", "AB-1234567", "NL123456B01"]:
            encrypted = service.encrypt(tax_id)
            assert service.decrypt(encrypted) == tax_id

    def test_different_encryptions_of_same_value(self, service: DonorTaxIDService) -> None:
        # Fernet includes timestamp+nonce, so same plaintext produces different tokens
        tax_id = "123456789"
        enc1 = service.encrypt(tax_id)
        enc2 = service.encrypt(tax_id)
        assert enc1 != enc2  # should differ due to random IV
        assert service.decrypt(enc1) == tax_id
        assert service.decrypt(enc2) == tax_id

    def test_decrypt_wrong_key_raises(self, fernet_key: str) -> None:
        svc1 = DonorTaxIDService(fernet_key)
        svc2 = DonorTaxIDService(Fernet.generate_key().decode())
        encrypted = svc1.encrypt("123456789")
        with pytest.raises(TaxIDDecryptionError):
            svc2.decrypt(encrypted)

    def test_decrypt_corrupted_token_raises(self, service: DonorTaxIDService) -> None:
        with pytest.raises(TaxIDDecryptionError):
            service.decrypt("not-a-valid-fernet-token")

    def test_decrypt_empty_string_raises(self, service: DonorTaxIDService) -> None:
        with pytest.raises(TaxIDDecryptionError):
            service.decrypt("")


# ---------------------------------------------------------------------------
# validate_tax_id
# ---------------------------------------------------------------------------


class TestValidateTaxId:
    # Valid cases
    def test_valid_bsn_8_digits(self) -> None:
        DonorTaxIDService.validate_tax_id("12345678", "BSN")

    def test_valid_bsn_9_digits(self) -> None:
        DonorTaxIDService.validate_tax_id("123456789", "BSN")

    def test_valid_tin(self) -> None:
        DonorTaxIDService.validate_tax_id("DE123456789", "TIN")

    def test_valid_cpf(self) -> None:
        DonorTaxIDService.validate_tax_id("12345678901", "CPF")

    def test_valid_nif(self) -> None:
        DonorTaxIDService.validate_tax_id("A12345678", "NIF")

    def test_valid_nino(self) -> None:
        DonorTaxIDService.validate_tax_id("AB123456C", "NINO")

    def test_valid_other(self) -> None:
        DonorTaxIDService.validate_tax_id("ABCD1234", "OTHER")

    # Invalid type
    def test_unknown_type_raises(self) -> None:
        with pytest.raises(TaxIDValidationError, match="Unknown tax_id_type"):
            DonorTaxIDService.validate_tax_id("123456789", "INVALID")

    def test_empty_type_raises(self) -> None:
        with pytest.raises(TaxIDValidationError, match="Unknown tax_id_type"):
            DonorTaxIDService.validate_tax_id("123456789", "")

    # BSN-specific
    def test_bsn_with_letters_raises(self) -> None:
        with pytest.raises(TaxIDValidationError, match="only digits"):
            DonorTaxIDService.validate_tax_id("12345678A", "BSN")

    def test_bsn_too_short_raises(self) -> None:
        short = "1" * (BSN_MIN_LENGTH - 1)
        with pytest.raises(TaxIDValidationError):
            DonorTaxIDService.validate_tax_id(short, "BSN")

    def test_bsn_too_long_raises(self) -> None:
        long_bsn = "1" * (BSN_MAX_LENGTH + 1)
        with pytest.raises(TaxIDValidationError):
            DonorTaxIDService.validate_tax_id(long_bsn, "BSN")

    # Length bounds
    def test_too_short_raises(self) -> None:
        with pytest.raises(TaxIDValidationError, match="too short"):
            DonorTaxIDService.validate_tax_id("AB", "TIN")

    def test_too_long_raises(self) -> None:
        with pytest.raises(TaxIDValidationError, match="too long"):
            DonorTaxIDService.validate_tax_id("A" * 21, "TIN")

    def test_maximum_length_valid(self) -> None:
        DonorTaxIDService.validate_tax_id("A" * 20, "OTHER")

    def test_minimum_length_valid(self) -> None:
        DonorTaxIDService.validate_tax_id("ABCD", "OTHER")
