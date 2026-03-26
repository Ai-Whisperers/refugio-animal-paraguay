# Rule: Clean Code Principles
**ID**: rule.clean-code.v1
**Version**: 1.0.0
**Applies to**: All source code in this repository

---

## Core Principles

### 1. Constants Over Magic Values

```python
# ❌ BAD — What does 30 mean? Why 30?
if adoption_request.days_pending > 30:
    notify_staff()

# ✅ GOOD — Intent is clear
ADOPTION_REVIEW_DEADLINE_DAYS = 30

if adoption_request.days_pending > ADOPTION_REVIEW_DEADLINE_DAYS:
    notify_staff()
```

- Define constants at the top of file or in a dedicated `constants.py`
- Constants in UPPER_SNAKE_CASE
- Group related constants together
- Add a comment if the value needs explanation

### 2. Meaningful Names

Names must answer: what is this, why does it exist, how is it used?

```python
# ❌ BAD
def process(d, t):
    x = d.get_all()
    for i in x:
        if i.s == t:
            return i

# ✅ GOOD
def find_animal_by_status(shelter_db: ShelterDatabase, status: AnimalStatus) -> Animal | None:
    all_animals = shelter_db.get_all_animals()
    for animal in all_animals:
        if animal.status == status:
            return animal
    return None
```

**Name rules**:
- Variables: noun describing what it contains (`donor_email`, not `de` or `email_field`)
- Functions: verb describing what it does (`validate_email`, not `email_check` or `do_validation`)
- Booleans: `is_`, `has_`, `can_`, `should_` prefix (`is_eligible_for_adoption`, not `eligible`)
- No generic names: `data`, `info`, `temp`, `result`, `value`, `item`, `thing`, `obj`
- No abbreviations unless universal (`id`, `url`, `html`, `db` are okay — `shltr`, `adptr` are not)

### 3. Single Responsibility

Each function/method does exactly **one** thing.

```python
# ❌ BAD — Three responsibilities: validate, save, notify
def submit_adoption_request(adopter, animal_id):
    if not adopter.email:
        raise ValueError("Email required")
    if adopter.age < 18:
        raise ValueError("Must be 18+")
    request = AdoptionRequest(adopter=adopter, animal_id=animal_id)
    db.save(request)
    email_service.send(adopter.email, "Application received")
    slack.notify(f"New adoption request for animal {animal_id}")

# ✅ GOOD — Composed from single-responsibility functions
def submit_adoption_request(adopter: Adopter, animal_id: int) -> AdoptionRequest:
    validate_adopter_eligibility(adopter)
    request = create_adoption_request(adopter, animal_id)
    save_adoption_request(request)
    notify_adoption_submitted(request)
    return request
```

**Signs a function has too many responsibilities**:
- You need a comment to explain what a section of the function does → extract that section
- Function name contains "and" → split at the "and"
- Function is longer than ~20 lines → likely doing too much
- Hard to test in isolation

### 4. DRY — Don't Repeat Yourself

Every piece of knowledge has a single authoritative location.

```python
# ❌ BAD — Validation logic duplicated in 3 places
def create_donor(email):
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        raise ValueError("Invalid email")
    ...

def update_donor_email(donor_id, email):
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        raise ValueError("Invalid email")
    ...

# ✅ GOOD — Single source of truth
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def validate_email(email: str) -> None:
    """Raises ValueError if email is not valid RFC 5322 format."""
    if not EMAIL_PATTERN.match(email):
        raise ValueError(f"Invalid email format: {email}")

def create_donor(email: str) -> Donor:
    validate_email(email)
    ...
```

DRY applies to:
- Validation logic
- Business rules
- Configuration values
- Error messages (use constants)
- URL patterns
- Database queries for the same data

### 5. Comment Standards

Comments explain **why**, not **what**. The code explains what.

```python
# ❌ BAD — Restates what the code does
# Loop through all animals and check status
for animal in animals:
    if animal.status == AnimalStatus.AVAILABLE:
        ...

# ✅ GOOD — Explains non-obvious reason
# EU donors require GDPR consent before adding to mailing list.
# This check must happen before payment processing, not after.
if donor.region == "EU" and not donor.has_gdpr_consent:
    raise GDPRConsentRequired(donor_id=donor.id)
```

**When to write a comment**:
- Non-obvious business rule: "Why" is not clear from code
- Tricky algorithm with subtle invariants
- Workaround for a bug in a dependency (include ticket ref)
- Performance optimization that sacrifices readability

**When NOT to write a comment**:
- When renaming a function would make it obvious
- To explain what a loop or condition does
- Version history (use git)
- TODO items belonging to a ticket (put in ticket instead)

### 6. Error Handling

Never silently swallow errors.

```python
# ❌ FORBIDDEN — Silent failure (bugs disappear)
try:
    send_adoption_confirmation(adopter.email)
except Exception:
    pass

# ❌ BAD — Comment-only failure (looks handled but isn't)
try:
    send_adoption_confirmation(adopter.email)
except Exception as e:
    # Notification failed, ignore
    pass

# ✅ GOOD — Log and continue (acceptable if notification is truly non-critical)
try:
    send_adoption_confirmation(adopter.email)
except EmailDeliveryError as e:
    logger.warning(
        "Adoption confirmation email failed — adopter will not be notified",
        extra={"adopter_id": adopter.id, "error": str(e)}
    )

# ✅ GOOD — Re-raise if this is critical
try:
    payment_result = process_donation(donor, amount)
except PaymentGatewayError as e:
    logger.error("Donation processing failed", extra={"donor_id": donor.id})
    raise  # Don't hide payment failures
```

Rules:
- Catch specific exceptions, not bare `except`
- Never catch `KeyboardInterrupt` with a bare `except`
- If you must catch and not re-raise: **log with context** (who, what, why it's okay)
- Critical operations (payment, data integrity): always re-raise or return structured error
- User-facing errors: specific, helpful messages (see quality-standards.md)

### 7. Function Size

A function should fit in one screen (~20-30 lines). If longer:
- Extract helper functions with descriptive names
- The calling function becomes a readable narrative

```python
# ✅ GOOD — Main function reads like a story
def process_adoption_application(application: AdoptionApplication) -> ApplicationResult:
    validate_application_completeness(application)
    check_adopter_eligibility(application.adopter)
    verify_animal_availability(application.animal_id)
    score = calculate_match_score(application)
    result = create_application_record(application, score)
    notify_stakeholders(result)
    return result
```

### 8. Type Hints (Python) / Types (TypeScript)

All function signatures must have type annotations.

```python
# ❌ BAD
def get_adoptable_animals(shelter_id, filters=None):
    ...

# ✅ GOOD
from typing import Optional
from .models import Animal, AnimalFilter, ShelterId

def get_adoptable_animals(
    shelter_id: ShelterId,
    filters: Optional[AnimalFilter] = None
) -> list[Animal]:
    ...
```

```typescript
// ❌ BAD
function processDonation(donor, amount, currency) { ... }

// ✅ GOOD
interface Donor { id: string; email: string; region: string; }
function processDonation(donor: Donor, amount: number, currency: Currency): DonationResult { ... }
```

---

## Anti-Patterns (Never Do)

```python
# ❌ Wildcard imports (pollutes namespace, hides dependencies)
from models import *

# ❌ Mutable default arguments (shared state bug)
def add_animal(shelter_id, tags=[]):
    tags.append("new")  # Mutates shared default!
    ...

# ❌ String concatenation in loops (O(n²))
result = ""
for animal in animals:
    result += str(animal) + ", "

# ❌ Using range(len()) (non-Pythonic)
for i in range(len(animals)):
    process(animals[i])

# ❌ Bare except (catches KeyboardInterrupt, SystemExit)
try:
    ...
except:
    pass

# ❌ Hardcoded credentials
PAYMENT_API_KEY = "sk_live_abc123def456"
```

```python
# ✅ Explicit imports
from models import Animal, Donor, AdoptionRequest

# ✅ Immutable defaults
def add_animal(shelter_id: int, tags: list[str] | None = None) -> Animal:
    if tags is None:
        tags = []
    ...

# ✅ String joining
result = ", ".join(str(animal) for animal in animals)

# ✅ Direct iteration
for animal in animals:
    process(animal)

# ✅ Specific exception handling
try:
    ...
except (ValidationError, DatabaseError) as e:
    handle_error(e)

# ✅ Environment variables for secrets
import os
PAYMENT_API_KEY = os.environ["PAYMENT_API_KEY"]
```

---

## FINAL MUST-PASS CHECKLIST

Before marking code complete:
- [ ] No magic numbers/strings — named constants used
- [ ] All names reveal intent (no `data`, `temp`, `x`, `i` outside loops)
- [ ] Each function does one thing (single responsibility)
- [ ] No duplicated business logic
- [ ] No bare `except:` clauses
- [ ] No silent error swallowing without logging
- [ ] All function signatures have type annotations
- [ ] No mutable default arguments
- [ ] No wildcard imports
- [ ] No hardcoded credentials or config
