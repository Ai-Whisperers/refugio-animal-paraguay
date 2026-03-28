"""Donor tax ID secure storage service.

Provides encrypt/decrypt operations for donor BSN/TIN numbers.
Tax IDs are sensitive personal data (GDPR Article 9-equivalent PII for
Dutch citizens) and must be encrypted at rest.

Encryption scheme: Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256).
The key is stored in the DONOR_TAX_ID_ENCRYPTION_KEY environment variable and
must never be committed to version control.
"""

import logging
from typing import Final

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Supported tax ID type identifiers
VALID_TAX_ID_TYPES: Final[frozenset[str]] = frozenset({"BSN", "TIN", "CPF", "NIF", "NINO", "OTHER"})

# BSN is exactly 8 or 9 digits
BSN_MIN_LENGTH: Final[int] = 8
BSN_MAX_LENGTH: Final[int] = 9
TAX_ID_MIN_LENGTH: Final[int] = 4
TAX_ID_MAX_LENGTH: Final[int] = 20


class TaxIDEncryptionKeyNotConfiguredError(Exception):
    """Raised when the encryption key env var is not set."""


class TaxIDDecryptionError(Exception):
    """Raised when decryption fails — key mismatch or data corruption."""


class TaxIDValidationError(ValueError):
    """Raised when the tax ID or type fails basic validation."""


class DonorTaxIDService:
    """Handles encryption and decryption of donor tax identification numbers.

    The Fernet key must be provided at construction time (injected from
    settings). Pass the plaintext key string; this service handles
    encoding internally.
    """

    def __init__(self, encryption_key: str) -> None:
        if not encryption_key:
            raise TaxIDEncryptionKeyNotConfiguredError(
                "DONOR_TAX_ID_ENCRYPTION_KEY is not set. "
                "Generate one with: python3 -c 'from cryptography.fernet import Fernet; "
                "print(Fernet.generate_key().decode())'"
            )
        self._fernet = Fernet(encryption_key.encode())

    def encrypt(self, plaintext_tax_id: str) -> str:
        """Encrypt a tax ID and return the Fernet token as a UTF-8 string."""
        token: bytes = self._fernet.encrypt(plaintext_tax_id.encode())
        return token.decode()

    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt a stored Fernet token and return the plaintext tax ID.

        Raises TaxIDDecryptionError if the token is invalid or the key does
        not match the key used for encryption.
        """
        try:
            plaintext: bytes = self._fernet.decrypt(encrypted_token.encode())
        except InvalidToken as exc:
            logger.error("Tax ID decryption failed — key mismatch or corrupted token")
            raise TaxIDDecryptionError(
                "Unable to decrypt tax ID: key mismatch or corrupted data."
            ) from exc
        return plaintext.decode()

    @staticmethod
    def validate_tax_id(tax_id: str, tax_id_type: str) -> None:
        """Validate tax ID value and type.

        Raises TaxIDValidationError if validation fails.
        Does NOT verify the mathematical checksum (e.g. BSN 11-proef);
        that is intentionally left to integration-layer validation.
        """
        if tax_id_type not in VALID_TAX_ID_TYPES:
            raise TaxIDValidationError(
                f"Unknown tax_id_type {tax_id_type!r}. "
                f"Allowed values: {sorted(VALID_TAX_ID_TYPES)}"
            )

        stripped = tax_id.strip()
        if len(stripped) < TAX_ID_MIN_LENGTH:
            raise TaxIDValidationError(
                f"Tax ID is too short (minimum {TAX_ID_MIN_LENGTH} characters)."
            )
        if len(stripped) > TAX_ID_MAX_LENGTH:
            raise TaxIDValidationError(
                f"Tax ID is too long (maximum {TAX_ID_MAX_LENGTH} characters)."
            )

        if tax_id_type == "BSN":
            if not stripped.isdigit():
                raise TaxIDValidationError("BSN must contain only digits.")
            if not (BSN_MIN_LENGTH <= len(stripped) <= BSN_MAX_LENGTH):
                raise TaxIDValidationError(
                    f"BSN must be {BSN_MIN_LENGTH}-{BSN_MAX_LENGTH} digits, "
                    f"got {len(stripped)}."
                )
