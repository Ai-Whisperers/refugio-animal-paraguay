---
story: RAP-411
epic: EPIC-73
title: "Audit and fix API input validation gaps"
status: ready
priority: 1
points: 3
created: 2026-03-27
---

# RAP-411: Audit and Fix API Input Validation Gaps

## Story

As a **backend developer**, I want **comprehensive input validation on all API endpoints** so that **invalid data is rejected at the boundary, not processed by business logic**.

## Description

API endpoints have gaps in validation. Some accept invalid data that should be rejected:
- Email fields accepted without format validation
- Phone numbers stored without format checking
- Money amounts (amount_cents) accepted as negative or zero
- Status fields don't validate against enum values
- String lengths have no limits
- Password reset endpoint has hardcoded localhost URL

All POST/PATCH endpoints must validate input before processing.

## Acceptance Criteria

### Email Validation

**Given** API endpoint with email field (e.g., donor email, adopter email)
**When** endpoint is called with email value
**Then**
- [ ] Email format is validated using `EmailStr` (Pydantic built-in)
- [ ] Invalid emails rejected: "notanemail", "user@", "@domain.com", "user @domain.com"
- [ ] Error response: `{"detail": "Invalid email format", "error_code": "INVALID_EMAIL"}`

**Pattern in schema**:
```python
from pydantic import BaseModel, EmailStr

class CreateDonorSchema(BaseModel):
    email: EmailStr  # Validates RFC 5322 format
    name: str
```

**Audit checklist**:
- [ ] All donor endpoints (create, update)
- [ ] All adopter endpoints (create, update)
- [ ] All user endpoints (create, update)
- [ ] Newsletter subscription endpoints
- [ ] Contact form endpoint

### Phone Number Validation

**Given** API endpoint with phone_number field
**When** endpoint is called with phone value
**Then**
- [ ] Phone is validated for format (ParaguAY: +595 XXX XXXX or 0XXX XXXX)
- [ ] Non-numeric characters rejected
- [ ] Invalid phone numbers rejected with clear error
- [ ] Optional: phone is normalized (+595 prefix, hyphens removed)

**Pattern in schema**:
```python
from pydantic import BaseModel, field_validator
import re

class ContactSchema(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        # Allow: +595 XXX XXXX or 0XXX XXXX
        if not re.match(r"^(\+595|0)\d{9}$", v.replace(" ", "").replace("-", "")):
            raise ValueError("Invalid phone number format")
        return v.replace(" ", "").replace("-", "")
```

**Audit checklist**:
- [ ] All volunteer registration endpoints
- [ ] Contact form endpoints
- [ ] User profile endpoints with phone field

### Amount Validation (Money Fields)

**Given** API endpoint with amount_cents field (e.g., donation amount)
**When** endpoint is called with amount
**Then**
- [ ] amount_cents > 0 is enforced (no zero, no negative)
- [ ] amount_cents is integer (no fractional cents)
- [ ] Large amounts are capped (e.g., max 999,999.99 EUR)
- [ ] Error: `{"detail": "Amount must be greater than 0", "error_code": "INVALID_AMOUNT"}`

**Pattern in schema**:
```python
from pydantic import BaseModel, field_validator

class CreateDonationSchema(BaseModel):
    amount_cents: int  # In cents: 5000 = $50.00

    @field_validator("amount_cents")
    @classmethod
    def validate_amount(cls, v):
        MIN_AMOUNT_CENTS = 100  # $1.00 minimum
        MAX_AMOUNT_CENTS = 99999900  # $999,999.00 maximum
        if v < MIN_AMOUNT_CENTS:
            raise ValueError("Amount must be at least $1.00")
        if v > MAX_AMOUNT_CENTS:
            raise ValueError("Amount exceeds maximum")
        return v
```

**Audit checklist**:
- [ ] All donation endpoints
- [ ] All payment endpoints
- [ ] Campaign fundraising goal validation

### Enum Validation (Status Fields)

**Given** API endpoint with status field (e.g., adoption_request status)
**When** endpoint is called with status value
**Then**
- [ ] Status is validated against allowed enum values
- [ ] Invalid status rejected: `{"detail": "Invalid status", "error_code": "INVALID_STATUS"}`
- [ ] Error lists allowed values: `allowed: ["pending", "approved", "rejected"]`

**Pattern in schema**:
```python
from enum import Enum
from pydantic import BaseModel

class AdoptionRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UpdateAdoptionRequestSchema(BaseModel):
    status: AdoptionRequestStatus  # Validates against enum
```

**Audit checklist**:
- [ ] Adoption request status (pending, approved, rejected, cancelled, completed)
- [ ] Animal status (available, reserved, adopted, unavailable, medical_hold)
- [ ] Campaign status (active, paused, completed, archived)
- [ ] Donation status (pending, completed, failed, refunded)

### String Length Validation

**Given** API endpoint with string fields (name, description, etc.)
**When** endpoint is called with very long string
**Then**
- [ ] String length limits are enforced
- [ ] Max length for name fields: 100 characters
- [ ] Max length for description/bio: 500 characters
- [ ] Error: `{"detail": "Name too long (max 100 chars)", "error_code": "FIELD_TOO_LONG"}`

**Pattern in schema**:
```python
from pydantic import BaseModel, StringConstraints
from typing import Annotated

class CreateAnimalSchema(BaseModel):
    name: Annotated[str, StringConstraints(max_length=100)]
    description: Annotated[str, StringConstraints(max_length=500)]
```

**Audit checklist**:
- [ ] All name fields (animal, adopter, donor, volunteer)
- [ ] All description/bio fields
- [ ] All address fields (max 200 characters)

### Password Validation

**Given** password reset endpoint
**When** new password is submitted
**Then**
- [ ] Password length ≥ 8 characters
- [ ] Password contains at least one uppercase letter
- [ ] Password contains at least one digit
- [ ] Password contains at least one special character (!@#$%^&*)
- [ ] All violations are listed in error response

**Pattern in schema**:
```python
from pydantic import BaseModel, field_validator
import re

class PasswordResetConfirmSchema(BaseModel):
    password: str
    password_confirm: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("at least one uppercase letter")
        if not re.search(r"\d", v):
            errors.append("at least one digit")
        if not re.search(r"[!@#$%^&*]", v):
            errors.append("at least one special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v

    @field_validator("password_confirm")
    @classmethod
    def validate_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords must match")
        return v
```

### Fix: Password Reset Localhost Hardcode

**Given** password_reset.py with hardcoded localhost URL
**When** password reset link is generated
**Then**
- [ ] URL is built from config: `FRONTEND_URL` (e.g., from env var)
- [ ] No hardcoded "localhost" in code
- [ ] URL pattern: `{FRONTEND_URL}/reset-password?token={token}`
- [ ] Works in development, staging, and production (uses correct domain)

**Pattern**:
```python
# In config.py
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# In password_reset_service.py
def generate_reset_link(token: str) -> str:
    return f"{FRONTEND_URL}/reset-password?token={token}"
```

### Required Field Validation

**Given** API endpoint with required fields
**When** endpoint is called without required field
**Then**
- [ ] Request is rejected with 422 Unprocessable Entity
- [ ] Error specifies which field is missing
- [ ] Error message: `"field_required": "This field is required"`

**Pydantic handles this automatically with required fields**:
```python
class CreateAdopterSchema(BaseModel):
    name: str  # Required (no default)
    email: EmailStr  # Required
    age: int = None  # Optional (has default)
```

## Definition of Done

- [ ] All validation gaps audited and documented in progress.md
- [ ] All POST/PATCH endpoints have input validation
- [ ] Email validation on all email fields
- [ ] Phone validation on all phone fields
- [ ] Amount validation on all money fields
- [ ] Status enum validation on all status fields
- [ ] String length validation on all text fields
- [ ] Password validation on password reset
- [ ] No localhost hardcode in any endpoint
- [ ] All endpoints return 422 Unprocessable Entity for validation errors
- [ ] Error responses include error_code and human-readable message
- [ ] All schemas use Pydantic v2 validators
- [ ] Linting passes (Ruff)
- [ ] Type checking passes (mypy)
- [ ] Code review approved

## Technical Notes

### Files to Create/Modify
- `src/api/` — All router files (create, update endpoints)
- `src/schemas.py` or per-router schema files
- `src/config.py` — Add FRONTEND_URL config
- `src/exceptions.py` — Validation error class (if not exists)

### Pydantic v2 Validators

**Old style (v1)**:
```python
@validator("email")
def validate_email(cls, v):
    ...
```

**New style (v2)**:
```python
@field_validator("email")
@classmethod
def validate_email(cls, v):
    ...
```

### Testing Validation

Tests should verify all invalid inputs are rejected:
```python
def test_reject_invalid_email():
    with pytest.raises(ValidationError):
        CreateDonorSchema(email="notanemail", name="John")

def test_reject_negative_amount():
    with pytest.raises(ValidationError):
        CreateDonationSchema(amount_cents=-100)
```

---

*Last updated: 2026-03-27*
