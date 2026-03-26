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

**Unit tests**: validation functions, business logic, data transformations, error conditions.
**Integration tests**: service + database interactions, API endpoint handlers, multi-service workflows.
**E2E tests**: critical user journeys (donation flow, adoption submission), smoke tests post-deploy.

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
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
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
class TestAdoptions:
    animals = []  # shared — test order matters!

    def test_add_animal(self):
        self.animals.append(Animal())  # leaks to next test

# ❌ Skipping tests with no justification
@pytest.mark.skip  # Why? No reason given.
def test_payment_processing():
    ...
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
