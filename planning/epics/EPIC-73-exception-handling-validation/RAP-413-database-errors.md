---
story: RAP-413
epic: EPIC-73
title: "Add database constraint error handling"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-413: Add Database Constraint Error Handling

## Story

As a **backend developer**, I want **proper handling of database constraint violations** so that **clients receive clear error messages instead of 500 errors**.

## Description

Database constraint violations (duplicate keys, foreign key violations, check constraints) currently bubble up as 500 Internal Server Error. They should be caught and converted to appropriate 4xx responses with clear error messages.

## Acceptance Criteria

### IntegrityError Handling (Duplicate Keys)

**Given** attempt to create a donor with email that already exists
**When** POST /donors with duplicate email
**Then**
- [ ] Database IntegrityError is caught (not bare Exception)
- [ ] Response is 409 Conflict (not 500)
- [ ] Error message: `{"detail": "Donor with this email already exists", "error_code": "DUPLICATE_EMAIL"}`
- [ ] No internal database error details exposed

**Pattern in endpoint**:
```python
from sqlalchemy.exc import IntegrityError
from src.api.error_handlers import APIException

@router.post("/donors")
async def create_donor(donor: CreateDonorSchema, db: Session):
    try:
        new_donor = Donor(**donor.model_dump())
        db.add(new_donor)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e.orig):
            raise APIException(
                detail="A donor with this email already exists",
                error_code="DUPLICATE_EMAIL",
                status_code=409,
            )
        elif "phone" in str(e.orig):
            raise APIException(
                detail="A donor with this phone number already exists",
                error_code="DUPLICATE_PHONE",
                status_code=409,
            )
        else:
            raise APIException(
                detail="Duplicate record (constraint violation)",
                error_code="DUPLICATE_RECORD",
                status_code=409,
            )
    return new_donor
```

**Audit checklist** — Find all db.commit() calls in create/update endpoints:
- [ ] `src/api/donors.py` — Unique email, unique phone
- [ ] `src/api/animals.py` — Unique microchip, unique ID
- [ ] `src/api/users.py` — Unique email
- [ ] `src/api/adoption_requests.py` — One pending per adopter+animal combination
- [ ] `src/api/campaigns.py` — Unique campaign slug/name

### ForeignKeyError Handling

**Given** attempt to adopt a nonexistent animal
**When** POST /adoption_requests with invalid animal_id
**Then**
- [ ] ForeignKeyError is caught (not 500)
- [ ] Response is 422 Unprocessable Entity (validation-like error)
- [ ] Error message: `{"detail": "Animal not found", "error_code": "ANIMAL_NOT_FOUND"}`

**Pattern**:
```python
from sqlalchemy.exc import ForeignKeyConstraintViolation

try:
    new_request = AdoptionRequest(
        adopter_id=adopter_id,
        animal_id=animal_id,  # May not exist
    )
    db.add(new_request)
    await db.commit()
except ForeignKeyConstraintViolation as e:
    await db.rollback()
    if "animal_id" in str(e.orig):
        raise APIException(
            detail="Animal not found",
            error_code="ANIMAL_NOT_FOUND",
            status_code=404,
        )
    elif "adopter_id" in str(e.orig):
        raise APIException(
            detail="Adopter not found",
            error_code="ADOPTER_NOT_FOUND",
            status_code=404,
        )
    else:
        raise APIException(
            detail="Referenced record not found",
            error_code="RECORD_NOT_FOUND",
            status_code=404,
        )
```

**Audit checklist** — Find all endpoints that insert with foreign keys:
- [ ] adoption_requests (adopter_id, animal_id)
- [ ] sponsorships (donor_id, animal_id)
- [ ] donations (campaign_id, donor_id)
- [ ] follow_ups (adopter_id)
- [ ] all others with FK columns

### Check Constraint Violations

**Given** attempt to create adoption request for unavailable animal
**When** constraint requires animal.status = AVAILABLE
**Then**
- [ ] Check constraint error is caught
- [ ] Response is 409 Conflict
- [ ] Error message: `{"detail": "Animal is not available for adoption", "error_code": "ANIMAL_NOT_AVAILABLE"}`

**Pattern**:
```python
from sqlalchemy.exc import IntegrityError

try:
    db.execute(
        insert(AdoptionRequest).values(
            adopter_id=adopter_id,
            animal_id=animal_id,
        )
    )
    await db.commit()
except IntegrityError as e:
    await db.rollback()
    if "animal_status" in str(e.orig) or "AVAILABLE" in str(e.orig):
        raise APIException(
            detail="Animal is not available for adoption",
            error_code="ANIMAL_NOT_AVAILABLE",
            status_code=409,
        )
```

### OperationalError Handling (Database Locked, Connection Lost)

**Given** database is locked or connection lost during write
**When** any POST/PATCH endpoint attempts commit
**Then**
- [ ] OperationalError is caught (not 500)
- [ ] Response is 503 Service Unavailable (not 500)
- [ ] Error message: `{"detail": "Database temporarily unavailable, please retry", "error_code": "DATABASE_UNAVAILABLE"}`
- [ ] Error is logged with full context

**Pattern**:
```python
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)

try:
    db.add(new_record)
    await db.commit()
except OperationalError as e:
    await db.rollback()
    logger.error(
        "database_operational_error",
        error_message=str(e),
        operation="create_donation",
    )
    raise APIException(
        detail="Database temporarily unavailable. Please retry in a moment.",
        error_code="DATABASE_UNAVAILABLE",
        status_code=503,
    )
```

### DataError Handling (Invalid Data Type)

**Given** attempt to insert invalid data type (e.g., non-numeric string into numeric field)
**When** POST endpoint receives bad data that passes JSON parsing
**Then**
- [ ] DataError is caught
- [ ] Response is 422 Unprocessable Entity
- [ ] Error message: `{"detail": "Invalid data format", "error_code": "INVALID_DATA_FORMAT"}`

**Pattern**:
```python
from sqlalchemy.exc import DataError

try:
    db.add(new_record)
    await db.commit()
except DataError as e:
    await db.rollback()
    raise APIException(
        detail="Invalid data format for one or more fields",
        error_code="INVALID_DATA_FORMAT",
        status_code=422,
    )
```

### Rollback on All Errors

**Given** any database error occurs during commit
**When** exception is caught
**Then**
- [ ] Transaction is rolled back: `await db.rollback()`
- [ ] Session is not left in inconsistent state
- [ ] No partial writes occur

**Critical**: All try/except blocks with db.add/commit must include rollback.

### Database Error Logging

All database errors must be logged with structured context:

```json
{
  "level": "ERROR",
  "operation": "create_donation",
  "error_type": "IntegrityError",
  "error_code": "DUPLICATE_EMAIL",
  "constraint": "donors_email_unique",
  "user_id": "user-123",
  "timestamp": "2026-03-27T15:30:45Z"
}
```

### Global Exception Handler for Database Errors

Add to `src/api/error_handlers.py`:

```python
from sqlalchemy.exc import (
    IntegrityError,
    ForeignKeyConstraintViolation,
    OperationalError,
    DataError,
)
from src.api.error_handlers import APIException

async def handle_integrity_error(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    await db.rollback()  # Rollback transaction

    error_str = str(exc.orig).lower()
    if "unique" in error_str or "duplicate" in error_str:
        detail = "Duplicate record: this value already exists"
        error_code = "DUPLICATE_RECORD"
    else:
        detail = "Data constraint violation"
        error_code = "CONSTRAINT_VIOLATION"

    logger.error(
        "database_integrity_error",
        error_code=error_code,
        constraint=getattr(exc.orig, "constraint", None),
    )

    return JSONResponse(
        status_code=409,
        content={
            "detail": detail,
            "error_code": error_code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

# Register all handlers
app.add_exception_handler(IntegrityError, handle_integrity_error)
app.add_exception_handler(OperationalError, handle_operational_error)
app.add_exception_handler(DataError, handle_data_error)
```

## Definition of Done

- [ ] All database error types identified and documented
- [ ] All IntegrityError (duplicates) handled with 409 Conflict
- [ ] All ForeignKeyError (missing references) handled with 404 Not Found
- [ ] All OperationalError (DB locked) handled with 503 Service Unavailable
- [ ] All DataError (invalid type) handled with 422 Unprocessable Entity
- [ ] All error paths include rollback: `await db.rollback()`
- [ ] All errors logged with structured context
- [ ] No raw database error details exposed to clients
- [ ] Code review approved
- [ ] CI pipeline passes

## Technical Notes

### Files to Modify
- `src/api/error_handlers.py` — Add global database error handlers
- All routers in `src/api/` with create/update endpoints

### SQLAlchemy Exception Types

Reference for error detection:
```python
from sqlalchemy.exc import (
    IntegrityError,           # Unique, check, FK violations
    ForeignKeyConstraintViolation,  # Foreign key violations
    OperationalError,         # DB locked, connection lost
    DataError,                # Invalid data type
    ProgrammingError,         # SQL syntax error
    DatabaseError,            # Base class
)
```

### Testing Database Errors

Unit tests will verify error handling (see EPIC-72 integration tests).

Example test:
```python
@pytest.mark.asyncio
async def test_duplicate_email_returns_409(db_session):
    donor1 = DonorFactory(email="test@example.com")
    db_session.add(donor1)
    await db_session.commit()

    # Attempt to create duplicate
    with pytest.raises(APIException) as exc_info:
        await create_donor(
            CreateDonorSchema(email="test@example.com", name="John"),
            db_session,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.error_code == "DUPLICATE_EMAIL"
```

---

*Last updated: 2026-03-27*
