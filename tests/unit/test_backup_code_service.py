"""Unit tests for src/services/backup_code_service.py."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from src.services.backup_code_service import (
    BACKUP_CODE_ALPHABET,
    BACKUP_CODE_LENGTH,
    _generate_raw_code,
    count_remaining_backup_codes,
    generate_backup_codes,
    use_backup_code,
)

# ---------------------------------------------------------------------------
# _generate_raw_code
# ---------------------------------------------------------------------------


class TestGenerateRawCode:
    def test_returns_correct_length(self) -> None:
        code = _generate_raw_code()
        assert len(code) == BACKUP_CODE_LENGTH

    def test_contains_only_valid_characters(self) -> None:
        safe_chars = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
        code = _generate_raw_code()
        for char in code:
            assert char in safe_chars

    def test_excludes_ambiguous_characters(self) -> None:
        """Ambiguous chars (0/O, 1/I/L) must never appear."""
        ambiguous = set("0O1IL")
        for _ in range(500):
            code = _generate_raw_code()
            assert not ambiguous.intersection(set(code)), f"Ambiguous char found in: {code}"

    def test_all_uppercase(self) -> None:
        code = _generate_raw_code()
        assert code == code.upper()

    def test_codes_are_random(self) -> None:
        """Generate 20 codes — at least two must differ (astronomically unlikely to collide)."""
        codes = {_generate_raw_code() for _ in range(20)}
        assert len(codes) > 1

    def test_backup_code_length_constant_is_8(self) -> None:
        assert BACKUP_CODE_LENGTH == 8

    def test_backup_code_alphabet_is_nonempty_string(self) -> None:
        """BACKUP_CODE_ALPHABET is a non-empty string constant (module-level)."""
        assert isinstance(BACKUP_CODE_ALPHABET, str)
        assert len(BACKUP_CODE_ALPHABET) > 0


# ---------------------------------------------------------------------------
# generate_backup_codes
# ---------------------------------------------------------------------------


class TestGenerateBackupCodes:
    @pytest.mark.asyncio
    async def test_returns_list_of_codes(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            codes = await generate_backup_codes(db, uuid4())

        assert isinstance(codes, list)

    @pytest.mark.asyncio
    async def test_returns_backup_code_count_codes(self) -> None:
        from src.db.models.totp_backup_code import BACKUP_CODE_COUNT

        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            codes = await generate_backup_codes(db, uuid4())

        assert len(codes) == BACKUP_CODE_COUNT

    @pytest.mark.asyncio
    async def test_deletes_existing_codes_first(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()

        user_id = uuid4()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            await generate_backup_codes(db, user_id)

        # execute() must have been called at least once (for the DELETE)
        db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_adds_code_objects_to_session(self) -> None:
        from src.db.models.totp_backup_code import BACKUP_CODE_COUNT

        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.add = MagicMock()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            await generate_backup_codes(db, uuid4())

        assert db.add.call_count == BACKUP_CODE_COUNT

    @pytest.mark.asyncio
    async def test_flushes_after_inserts(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.add = MagicMock()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            await generate_backup_codes(db, uuid4())

        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_codes_are_strings(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            codes = await generate_backup_codes(db, uuid4())

        for code in codes:
            assert isinstance(code, str)

    @pytest.mark.asyncio
    async def test_plain_codes_have_correct_length(self) -> None:
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()

        with patch("src.services.backup_code_service.hash_password", return_value="hash"):
            codes = await generate_backup_codes(db, uuid4())

        for code in codes:
            assert len(code) == BACKUP_CODE_LENGTH


# ---------------------------------------------------------------------------
# use_backup_code
# ---------------------------------------------------------------------------


class TestUseBackupCode:
    def _make_mock_row(self, code_hash: str, used: bool = False) -> MagicMock:
        row = MagicMock()
        row.code_hash = code_hash
        row.used_at = "2026-01-01" if used else None
        return row

    @pytest.mark.asyncio
    async def test_returns_true_and_marks_used_on_match(self) -> None:
        row = self._make_mock_row("correct_hash")
        db = AsyncMock()
        db.flush = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute = AsyncMock(return_value=result_mock)

        with patch("src.services.backup_code_service.verify_password", return_value=True):
            result = await use_backup_code(db, uuid4(), "ABCD1234")

        assert result is True
        assert row.used_at is not None
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_no_unused_codes(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        with patch("src.services.backup_code_service.verify_password", return_value=False):
            result = await use_backup_code(db, uuid4(), "BADCODE1")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_hash_matches(self) -> None:
        rows = [self._make_mock_row("hash1"), self._make_mock_row("hash2")]
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = rows
        db.execute = AsyncMock(return_value=result_mock)

        with patch("src.services.backup_code_service.verify_password", return_value=False):
            result = await use_backup_code(db, uuid4(), "WRONGCODE")

        assert result is False

    @pytest.mark.asyncio
    async def test_strips_spaces_and_dashes_from_input(self) -> None:
        """Input normalisation: spaces, dashes, mixed case are sanitised."""
        row = self._make_mock_row("hash")
        db = AsyncMock()
        db.flush = AsyncMock()

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = [row]
        db.execute = AsyncMock(return_value=result_mock)

        captured: list[str] = []

        def fake_verify(plain: str, _hashed: str) -> bool:
            captured.append(plain)
            return True

        with patch("src.services.backup_code_service.verify_password", side_effect=fake_verify):
            await use_backup_code(db, uuid4(), "  ab-cd 12 34  ")

        # After normalisation the code should be stripped and uppercased
        assert captured[0] == "ABCD1234"

    @pytest.mark.asyncio
    async def test_does_not_flush_on_mismatch(self) -> None:
        db = AsyncMock()
        db.flush = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        with patch("src.services.backup_code_service.verify_password", return_value=False):
            await use_backup_code(db, uuid4(), "XXXXXXXX")

        db.flush.assert_not_awaited()


# ---------------------------------------------------------------------------
# count_remaining_backup_codes
# ---------------------------------------------------------------------------


class TestCountRemainingBackupCodes:
    @pytest.mark.asyncio
    async def test_returns_count_of_unused_codes(self) -> None:
        rows = [MagicMock(), MagicMock(), MagicMock()]
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = rows
        db.execute = AsyncMock(return_value=result_mock)

        count = await count_remaining_backup_codes(db, uuid4())

        assert count == 3

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_codes(self) -> None:
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result_mock)

        count = await count_remaining_backup_codes(db, uuid4())

        assert count == 0
