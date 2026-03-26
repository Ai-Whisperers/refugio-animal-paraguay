"""Unit tests for IBAN validation and masking utilities."""

from src.utils.iban import mask_iban, normalize_iban, validate_iban


class TestValidateIban:
    """Tests for IBAN format and checksum validation."""

    def test_valid_dutch_iban(self) -> None:
        assert validate_iban("NL91ABNA0417164300") is True

    def test_valid_german_iban(self) -> None:
        assert validate_iban("DE89370400440532013000") is True

    def test_valid_spanish_iban(self) -> None:
        assert validate_iban("ES9121000418450200051332") is True

    def test_valid_british_iban(self) -> None:
        assert validate_iban("GB29NWBK60161331926819") is True

    def test_valid_french_iban(self) -> None:
        assert validate_iban("FR7630006000011234567890189") is True

    def test_valid_iban_with_spaces(self) -> None:
        assert validate_iban("NL91 ABNA 0417 1643 00") is True

    def test_valid_iban_lowercase(self) -> None:
        assert validate_iban("nl91abna0417164300") is True

    def test_invalid_iban_wrong_checksum(self) -> None:
        assert validate_iban("NL00ABNA0417164300") is False

    def test_invalid_iban_too_short(self) -> None:
        assert validate_iban("NL91ABNA") is False

    def test_invalid_iban_wrong_length_for_country(self) -> None:
        # NL should be 18 chars, this is 20
        assert validate_iban("NL91ABNA041716430099") is False

    def test_invalid_iban_no_country(self) -> None:
        assert validate_iban("1234567890") is False

    def test_invalid_iban_empty(self) -> None:
        assert validate_iban("") is False

    def test_invalid_iban_special_chars(self) -> None:
        assert validate_iban("NL91-ABNA-0417-1643-00") is False


class TestNormalizeIban:
    """Tests for IBAN normalization."""

    def test_removes_spaces(self) -> None:
        assert normalize_iban("NL91 ABNA 0417 1643 00") == "NL91ABNA0417164300"

    def test_converts_to_uppercase(self) -> None:
        assert normalize_iban("nl91abna0417164300") == "NL91ABNA0417164300"


class TestMaskIban:
    """Tests for IBAN masking."""

    def test_masks_middle_portion(self) -> None:
        result = mask_iban("NL91ABNA0417164300")
        assert result == "NL91**********4300"

    def test_shows_first_4_and_last_4(self) -> None:
        result = mask_iban("DE89370400440532013000")
        assert result.startswith("DE89")
        assert result.endswith("3000")
        assert "*" in result

    def test_short_iban_returns_stars(self) -> None:
        assert mask_iban("NL91") == "****"

    def test_handles_spaces_in_input(self) -> None:
        result = mask_iban("NL91 ABNA 0417 1643 00")
        assert result == "NL91**********4300"
