---
name: testing-patterns
description: Testing standards, pytest patterns, fixtures, mocking, and coverage requirements
load-when: writing tests, generating test coverage, pytest, vitest, jest, fixtures, mocking
---

# Testing Patterns

Load this skill when writing tests, analyzing coverage, or designing test strategy.

## Core Testing Principles

- **Test behavior, not implementation** — tests should survive refactoring
- **One assertion per test** — or tightly related assertions for one behavior
- **Independent tests** — no shared mutable state between tests
- **Readable test names** — `test_raises_value_error_when_email_is_none` not `test_email_1`
- **Fast by default** — unit tests should run in <1s total; mock external services

## Test Pyramid

```
           /\
          /  \    E2E (few, slow, fragile)
         /----\
        /      \   Integration (moderate)
       /--------\
      /          \  Unit (many, fast, stable)
     /____________\
```

- **Unit**: Test one function/class in isolation. Mock all external dependencies.
- **Integration**: Test multiple layers together (e.g., service + DB). Use a test database.
- **E2E**: Test user-facing flows end-to-end. Keep minimal.

## pytest Patterns

### Basic Structure (AAA)

```python
def test_validate_email_accepts_valid_eu_email() -> None:
    # Arrange
    email = "donor@example.de"

    # Act
    result = validate_email(email)

    # Assert
    assert result is True
```

### Parametrize for Multiple Cases

```python
import pytest

@pytest.mark.parametrize("email,expected", [
    ("donor@example.com", True),
    ("user@mailinator.com", False),  # disposable domain
    ("", False),                      # empty string
    ("not-an-email", False),          # no @ symbol
    ("user@example.co.uk", True),     # international TLD
])
def test_validate_email(email: str, expected: bool) -> None:
    assert validate_email(email) == expected
```

### Fixtures

```python
import pytest
from typing import Generator
from myapp.db import Database


@pytest.fixture
def db() -> Generator[Database, None, None]:
    """Provide a test database with clean state per test."""
    database = Database(url="postgresql://test:test@localhost:5432/test_db")
    database.create_tables()
    yield database
    database.drop_all_tables()


@pytest.fixture
def sample_donor(db: Database) -> Donor:
    """Create a minimal valid donor for tests that need an existing donor."""
    return db.donors.create(
        email="test@example.com",
        name="Test Donor",
        region="EU",
    )
```

### Mocking External Services

```python
from unittest.mock import MagicMock, patch


def test_send_adoption_confirmation_email_on_approval() -> None:
    # Mock the email service — don't send real emails in tests
    with patch("myapp.notifications.email_service") as mock_email:
        mock_email.send.return_value = {"status": "sent"}

        process_adoption_approval(adoption_id=42)

        mock_email.send.assert_called_once_with(
            to="adopter@example.com",
            template="adoption_approved",
            context={"adoption_id": 42},
        )


def test_handles_email_service_failure_gracefully() -> None:
    with patch("myapp.notifications.email_service") as mock_email:
        mock_email.send.side_effect = EmailDeliveryError("SMTP connection failed")

        # Should not raise — notification failure is non-critical
        result = process_adoption_approval(adoption_id=42)

        assert result.status == "approved"
```

### Testing Exceptions

```python
def test_raises_not_found_for_unknown_animal() -> None:
    with pytest.raises(NotFoundError, match="Animal 999 not found"):
        get_animal(animal_id=999)


def test_raises_validation_error_for_underage_adopter() -> None:
    adopter = Adopter(age=16, email="teen@example.com")

    with pytest.raises(ValidationError) as exc_info:
        validate_adopter_eligibility(adopter)

    assert "minimum age" in str(exc_info.value).lower()
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_donation_processing() -> None:
    result = await process_donation_async(donor_id=1, amount=50.0)
    assert result.status == "completed"
```

## Coverage Requirements

| Scope | Threshold | Notes |
|-------|-----------|-------|
| Overall | 80% | Fail CI below this |
| Critical paths (payment, auth, data integrity) | 95% | Manual review required below |
| Utility functions | 90% | |
| New code in PRs | 80% | Never decrease overall |

```bash
# Check coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## What NOT to Test

- Framework code (Django ORM, SQLAlchemy session management)
- Simple getters/setters with no logic
- Third-party library behavior
- Code that only calls other already-tested functions

## Test File Naming

| Source file | Test file |
|-------------|-----------|
| `src/services/adoption.py` | `tests/services/test_adoption.py` |
| `src/utils/validation.py` | `tests/utils/test_validation.py` |
| `src/api/routes.py` | `tests/api/test_routes.py` |

## Integration Tests Pattern

```python
# tests/integration/test_adoption_flow.py
import pytest
from myapp.db import TestDatabase

@pytest.mark.integration
class TestAdoptionFlow:
    """Integration tests — require a real test database."""

    def test_full_adoption_request_flow(self, db: TestDatabase) -> None:
        # Create test data
        animal = db.animals.create(name="Buddy", status="available")
        adopter = db.adopters.create(email="adopter@example.com")

        # Execute the flow
        request = submit_adoption_request(adopter.id, animal.id)

        # Verify all side effects
        assert request.status == "pending"
        assert db.animals.get(animal.id).status == "reserved"
        assert db.notifications.count() == 1
```

Run integration tests separately:
```bash
pytest -m integration tests/integration/
pytest -m "not integration" tests/  # skip integration in fast runs
```
