"""IBAN validation and masking utilities.

Provides basic IBAN format validation and masking for GDPR-safe logging.
For production checksum validation, consider python-stdnum.
"""

import re

# Country-specific IBAN length requirements (ISO 13616)
_IBAN_LENGTHS: dict[str, int] = {
    "AL": 28,
    "AD": 24,
    "AT": 20,
    "AZ": 28,
    "BH": 22,
    "BY": 28,
    "BE": 16,
    "BA": 20,
    "BR": 29,
    "BG": 22,
    "CR": 22,
    "HR": 21,
    "CY": 28,
    "CZ": 24,
    "DK": 18,
    "DO": 28,
    "TL": 23,
    "EE": 20,
    "FO": 18,
    "FI": 18,
    "FR": 27,
    "GE": 22,
    "DE": 22,
    "GI": 23,
    "GR": 27,
    "GL": 18,
    "GT": 28,
    "HU": 28,
    "IS": 26,
    "IQ": 23,
    "IE": 22,
    "IL": 23,
    "IT": 27,
    "JO": 30,
    "KZ": 20,
    "XK": 20,
    "KW": 30,
    "LV": 21,
    "LB": 28,
    "LI": 21,
    "LT": 20,
    "LU": 20,
    "MK": 19,
    "MT": 31,
    "MR": 27,
    "MU": 30,
    "MC": 27,
    "MD": 24,
    "ME": 22,
    "NL": 18,
    "NO": 15,
    "PK": 24,
    "PS": 29,
    "PL": 28,
    "PT": 25,
    "QA": 29,
    "RO": 24,
    "SM": 27,
    "SA": 24,
    "RS": 22,
    "SC": 31,
    "SK": 24,
    "SI": 19,
    "ES": 24,
    "SE": 24,
    "CH": 21,
    "TN": 24,
    "TR": 26,
    "UA": 29,
    "AE": 23,
    "GB": 22,
    "VA": 22,
    "VG": 24,
}

# General IBAN format: 2 uppercase letters + 2 digits + 10-30 alphanumeric
_IBAN_GENERAL_PATTERN = re.compile(r"^[A-Z]{2}\d{2}[0-9A-Z]{10,30}$")


def validate_iban(iban: str) -> bool:
    """Validate IBAN format.

    Checks:
    1. General format (2 letter country + 2 check digits + BBAN)
    2. Country-specific length (if country is in the known list)
    3. ISO 7064 MOD-97-10 checksum

    Returns True if the IBAN is valid, False otherwise.
    """
    # Normalize: remove spaces and convert to uppercase
    iban = iban.replace(" ", "").upper()

    # Check general format
    if not _IBAN_GENERAL_PATTERN.match(iban):
        return False

    # Check country-specific length
    country_code = iban[:2]
    expected_length = _IBAN_LENGTHS.get(country_code)
    if expected_length is not None and len(iban) != expected_length:
        return False

    # ISO 7064 MOD-97-10 checksum validation
    # Move first 4 chars to end, convert letters to numbers (A=10, B=11, ...)
    rearranged = iban[4:] + iban[:4]
    numeric_str = ""
    for char in rearranged:
        if char.isdigit():
            numeric_str += char
        else:
            numeric_str += str(ord(char) - ord("A") + 10)

    return int(numeric_str) % 97 == 1


def normalize_iban(iban: str) -> str:
    """Normalize IBAN: remove spaces, convert to uppercase."""
    return iban.replace(" ", "").upper()


def mask_iban(iban: str) -> str:
    """Mask IBAN for GDPR-safe logging and display.

    Shows country code + check digits + last 4 characters only.
    Example: NL91ABNA0417164300 -> NL91************4300
    """
    iban = normalize_iban(iban)
    if len(iban) < 8:
        return "****"
    return f"{iban[:4]}{'*' * (len(iban) - 8)}{iban[-4:]}"
