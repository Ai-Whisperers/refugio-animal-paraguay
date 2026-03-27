---
story: RAP-406
epic: EPIC-72
title: "Improve adoption_requests test coverage (41% → 80%+)"
status: ready
priority: 0
points: 5
created: 2026-03-27
---

# RAP-406: Improve Adoption Requests Test Coverage

## Story

As a **developer**, I want **comprehensive tests for the adoption_requests module** so that **status transitions, contract generation, and edge cases are protected from regressions**.

## Description

The `adoption_requests` module is at 41% coverage. Critical logic is untested:
- Status transitions (pending → approved, pending → rejected, pending → cancelled)
- Contract document generation
- Duplicate request prevention
- Notification triggering on status changes
- Edge cases (adopting unavailable animal, adopter self-approving, invalid status transitions)

All of these need unit and integration tests.

## Acceptance Criteria

### Unit Tests (tests/unit/test_adoption_requests_service.py)

**Given** an adopter and available animal
**When** `create_adoption_request(adopter_id, animal_id)` is called
**Then**
- [ ] AdoptionRequest record is created with status=PENDING
- [ ] Request ID is unique and non-empty
- [ ] Created timestamp is set to current time
- [ ] Adopter is notified (email queued)

**Given** an adopter who already has a PENDING request for the same animal
**When** `create_adoption_request(adopter_id, animal_id)` is called again
**Then**
- [ ] `DuplicateRequestError` is raised
- [ ] No second request is created

**Given** an adopter trying to adopt an UNAVAILABLE animal
**When** `create_adoption_request(adopter_id, unavailable_animal_id)` is called
**Then**
- [ ] `AnimalNotAvailableError` is raised
- [ ] No request is created

**Given** a PENDING adoption request
**When** `approve_adoption_request(request_id, staff_member_id)` is called
**Then**
- [ ] Request status changes to APPROVED
- [ ] Animal status changes to RESERVED
- [ ] Contract PDF is generated
- [ ] Adopter is notified with contract link
- [ ] Request includes contract_signed_at = None (awaiting signature)

**Given** a PENDING adoption request
**When** `reject_adoption_request(request_id, staff_member_id, reason)` is called
**Then**
- [ ] Request status changes to REJECTED
- [ ] Animal status returns to AVAILABLE
- [ ] Adopter is notified with rejection reason
- [ ] Reason is stored and cannot be changed

**Given** a PENDING adoption request
**When** `cancel_adoption_request(request_id, initiator_id)` is called and initiator is the adopter
**Then**
- [ ] Request status changes to CANCELLED
- [ ] Animal status returns to AVAILABLE
- [ ] Staff is notified

**Given** a PENDING adoption request
**When** `cancel_adoption_request(request_id, staff_id)` is called and initiator is staff
**Then**
- [ ] Request status changes to CANCELLED
- [ ] Adopter is notified with cancellation reason

**Given** a REJECTED or CANCELLED request
**When** state transition is attempted (e.g., to APPROVED)
**Then**
- [ ] `InvalidStatusTransitionError` is raised
- [ ] No state change occurs

**Given** an APPROVED adoption request
**When** contract_signed=True and `finalize_adoption(request_id)` is called
**Then**
- [ ] Request status changes to COMPLETED
- [ ] Animal status changes to ADOPTED
- [ ] Animal's `adopted_by_id` is set to the adopter
- [ ] Animal's `adoption_date` is set to current date
- [ ] Adoption completion notification is sent
- [ ] Both adopter and staff receive confirmation

**Given** an APPROVED request without signed contract
**When** `finalize_adoption(request_id)` is called
**Then**
- [ ] `ContractNotSignedError` is raised
- [ ] Status does not change

**Given** an AdoptionRequest
**When** contract PDF is generated via `generate_adoption_contract(request_id)`
**Then**
- [ ] PDF file path is returned
- [ ] PDF contains: adopter name, animal name/ID, date, shelter details
- [ ] PDF is stored in `docs/adoption_contracts/` with unique filename
- [ ] PDF is not accessible publicly (not in webroot)

### Integration Tests (tests/integration/test_adoption_requests_flow.py)

**Given** a fresh adopter user and available animal
**When** full adoption workflow is executed (create → approve → sign contract → finalize)
**Then**
- [ ] All status transitions succeed
- [ ] Animal availability is correctly managed (reserved → adopted)
- [ ] All notifications are triggered
- [ ] Adoption appears in adopter's profile
- [ ] Adoption appears in animal's history

**Given** concurrent requests from two adopters for the same animal
**When** both submit requests simultaneously
**Then**
- [ ] First succeeds
- [ ] Second fails (animal becomes RESERVED after first approval)
- [ ] Both adopters are appropriately notified

**Given** an APPROVED adoption request
**When** adopter attempts to cancel
**Then**
- [ ] Cancellation is rejected (status immutable after approval)
- [ ] Adopter receives error message

**Given** an adoption request in PENDING status for >30 days
**When** automated cleanup job runs
**Then**
- [ ] Request is marked as EXPIRED (new status)
- [ ] Animal returns to AVAILABLE (if still RESERVED)
- [ ] Both parties are notified

### Notification Tests (tests/unit/test_adoption_request_notifications.py)

**Given** an adoption request is created
**When** notification event is triggered
**Then**
- [ ] Adopter email includes: animal details, request ID, next steps
- [ ] Staff email includes: adopter name, animal ID, review deadline
- [ ] In-app notification created for adopter
- [ ] Failure in email send does not block request creation (logged only)

**Given** an adoption request is approved
**When** notification event is triggered
**Then**
- [ ] Adopter receives contract PDF link
- [ ] Email includes: approval date, contract signature deadline (7 days)
- [ ] WhatsApp notification sent (if phone number available)

### Schema Tests (tests/unit/test_adoption_request_schemas.py)

**Given** CreateAdoptionRequestSchema with valid adopter_id and animal_id
**When** validated
**Then**
- [ ] Schema accepts it
- [ ] Both IDs are UUID format

**Given** CreateAdoptionRequestSchema with invalid UUIDs
**When** validated
**Then**
- [ ] Schema rejects it
- [ ] Error specifies "adopter_id must be valid UUID"

**Given** ApproveAdoptionRequestSchema
**When** validated without staff_member_id
**Then**
- [ ] Schema rejects it as required field

## Definition of Done

- [ ] All test files created and passing
- [ ] Coverage report shows adoption_requests module at ≥ 80%
- [ ] All tests follow AAA pattern
- [ ] No tests skipped without documented reason
- [ ] Mock animal availability checks; don't affect real animals
- [ ] Notifications mocked at service boundary (don't send real emails)
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Reference
- `src/api/adoption_requests.py` — Route handlers (main source of untested code)
- `src/services/adoption_requests_service.py` — Service logic
- `src/db/models/adoption_request.py` — Model definition
- `src/db/models/animal.py` — Animal status enum
- `src/notifications/adoption_request_handlers.py` — Notification triggers
- `tests/conftest.py` — Shared fixtures

### Files to Create
- `tests/unit/test_adoption_requests_service.py` — Service logic tests
- `tests/unit/test_adoption_request_schemas.py` — Schema validation tests
- `tests/unit/test_adoption_request_notifications.py` — Notification tests
- `tests/integration/test_adoption_requests_flow.py` — End-to-end flow tests

### Key Test Data

**Adopter fixtures**:
- `adopter_factory` — Create test adopters
- `adopter_age_18_plus` — Eligible adopter
- `adopter_underage` — Ineligible (for negative tests)

**Animal fixtures**:
- `animal_factory(status=AVAILABLE)` — Available animal
- `animal_factory(status=ADOPTED)` — Already adopted
- `animal_factory(status=RESERVED)` — Reserved by another request

**Request fixtures**:
- `adoption_request_factory(status=PENDING)` — Create various states
- `adoption_request_factory(status=APPROVED)`
- `adoption_request_factory(status=REJECTED)`

### Mocking Strategy

```python
# Mock notification handlers to avoid sending real emails
@patch("src.notifications.adoption_request_handlers.send_adopter_notification")
@patch("src.notifications.adoption_request_handlers.send_staff_notification")
def test_approval_triggers_notifications(mock_staff, mock_adopter, ...):
    # Test here
    mock_adopter.assert_called_once()

# Mock contract generation to avoid file I/O in tests
@patch("src.services.adoption_requests_service.generate_pdf")
def test_contract_generation(...):
    # Test returns mock PDF path
```

### Status Transition State Machine

Document the valid transitions to guide test coverage:

```
PENDING → APPROVED (by staff)
PENDING → REJECTED (by staff)
PENDING → CANCELLED (by adopter or staff)
APPROVED → COMPLETED (when contract signed)
APPROVED → CANCELLED (rare: adoption aborted)

Invalid: REJECTED → anything, CANCELLED → anything, etc.
```

---

*Last updated: 2026-03-27*
