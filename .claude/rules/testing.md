# Rule: Testing Standards
**ID**: rule.testing.standards.v1
**Version**: 1.0.0
**Applies to**: All test code and test strategy in this repository

---

## Test Pyramid

```
           /\
          /  \    E2E (few, slow — reserve for critical user journeys)
         /----\
        /      \   Integration (moderate — service + real DB)
       /--------\
      /          \  Unit (many, fast — pure logic, all deps mocked)
     /____________\
```

**Unit tests** cover:
- Validation functions
- Business logic / domain rules
- Data transformations
- Error conditions and edge cases

**Integration tests** cover:
- Service + database interactions
- API endpoint handlers
- Multi-service workflows

**E2E tests** cover (keep minimal):
- Critical user journeys (donation flow, adoption submission)
- Smoke tests post-deploy

---

## Coverage Requirements

| Scope | Threshold | Enforcement |
|-------|-----------|-------------|
| Overall project | 80% | CI fails below this |
| Critical paths (payment, auth, data integrity) | 95% | Manual review required below |
| Utility/validation functions | 90% | CI warning below |
| New code in any PR | 80% | PR blocked below this |

Coverage must **never decrease** with a merge to main.

```bash
# Run coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# HTML report for detailed analysis
pytest --cov=src --cov-report=html && open htmlcov/index.html
```

---

## Test File Structure

```
tests/
├── conftest.py           ← Shared fixtures (db, client, test data)
├── unit/
│   ├── test_validation.py
│   ├── test_adoption_service.py
│   └── test_donation_service.py
├── integration/
│   ├── test_adoption_flow.py
│   └── test_donation_flow.py
└── e2e/
    └── test_critical_journeys.py
```

**File naming**: `tests/{layer}/test_{module_name}.py` mirrors `src/{module_name}.py`

---

## Test Quality Standards

### Naming

```python
# ✅ Describes behavior
def test_validate_email_returns_false_for_disposable_domain() -> None:
def test_raises_validation_error_when_adopter_is_underage() -> None:
def test_donation_amount_rounds_to_two_decimal_places() -> None:

# ❌ Numbered, vague
def test_email_1() -> None:
def test_donation() -> None:
def test_valid() -> None:
```

### AAA Pattern

Every test follows Arrange → Act → Assert:

```python
def test_adoption_request_sets_animal_status_to_reserved() -> None:
    # Arrange
    animal = Animal(id=uuid4(), status=AnimalStatus.AVAILABLE)
    adopter = Adopter(id=uuid4(), email="adopter@example.com")

    # Act
    request = submit_adoption_request(adopter.id, animal.id)

    # Assert
    assert request.status == AdoptionRequestStatus.PENDING
    assert animal.status == AnimalStatus.RESERVED
```

### Fixture Discipline

```python
# conftest.py
import pytest
from typing import Generator
from myapp.db import Database

@pytest.fixture
def db() -> Generator[Database, None, None]:
    """Clean test database per test."""
    database = Database(url=TEST_DATABASE_URL)
    database.create_tables()
    yield database
    database.drop_all_tables()  # always clean up

@pytest.fixture
def sample_animal(db: Database) -> Animal:
    """Minimal valid animal for tests that need an existing record."""
    return db.animals.create(name="Buddy", status="available", species="dog")
```

### Mocking Rules

- Mock at the boundary (DB, HTTP, email service, filesystem) — not internal functions
- Never mock code you own unless it's at an I/O boundary
- Use `unittest.mock.patch` targeting the import path in the module under test

```python
# ✅ Mock the boundary, not the internals
with patch("src.notifications.email_service") as mock_email:
    mock_email.send.return_value = {"status": "sent"}
    result = process_adoption_approval(adoption_id=42)

# ❌ Mock an internal function (breaks when you refactor)
with patch("src.adoptions.validate_adopter") as mock_validate:
    ...
```

---

## Integration Tests

```python
# tests/integration/test_adoption_flow.py
import pytest
from myapp.db import TestDatabase

@pytest.mark.integration
class TestAdoptionFlow:
    """Integration tests — require real test database."""

    def test_full_adoption_request_flow(self, db: TestDatabase) -> None:
        animal = db.animals.create(name="Buddy", status="available")
        adopter = db.adopters.create(email="adopter@example.com")

        request = submit_adoption_request(adopter.id, animal.id)

        assert request.status == "pending"
        assert db.animals.get(animal.id).status == "reserved"
        assert db.notifications.count() == 1  # notification was queued
```

Run integration tests separately:

```bash
pytest -m integration tests/integration/    # only integration
pytest -m "not integration" tests/          # skip integration (fast CI)
```

---

## Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_send_donation_confirmation_async() -> None:
    result = await send_confirmation_email_async(donor_id="uuid", amount=50.0)
    assert result.status == "sent"
```

Install: `pip install pytest-asyncio` and configure `asyncio_mode = "auto"` in `pytest.ini`.

---

## Test Anti-Patterns

```python
# ❌ Test with no assertions (always passes)
def test_process_donation():
    process_donation(donor_id=1, amount=50.0)

# ❌ Testing implementation instead of behavior
def test_calls_validate_email():
    with patch("service.validate_email") as mock:
        submit_form(email="test@example.com")
    mock.assert_called_once()  # tests HOW, not WHAT

# ❌ Shared mutable state between tests
GLOBAL_DB = Database()  # mutated by one test, corrupts the next

class TestAdoptions:
    animals = []  # shared — test order matters!

    def test_add_animal(self):
        self.animals.append(Animal())  # leaks to next test

# ❌ Skipping tests with no justification
@pytest.mark.skip  # Why? No reason given.
def test_payment_processing():
    ...

# ❌ Over-asserting — fragile when implementation changes
def test_process_adoption():
    result = process_adoption(...)
    assert result.id is not None
    assert result.created_at is not None
    assert result.updated_at == result.created_at  # implementation detail
    assert result._internal_state == "initialized"  # private field!
```

---

## FINAL MUST-PASS CHECKLIST

Before committing test code:
- [ ] Test names describe behavior (`test_raises_X_when_Y`)
- [ ] Each test follows AAA pattern
- [ ] No shared mutable state between tests
- [ ] External dependencies mocked at I/O boundary only
- [ ] Integration tests marked with `@pytest.mark.integration`
- [ ] Coverage at or above threshold (`--cov-fail-under=80`)
- [ ] No skipped tests without a documented reason
- [ ] No tests that trivially pass without catching any bug
- [ ] Test files follow naming convention: `tests/{layer}/test_{module}.py`
