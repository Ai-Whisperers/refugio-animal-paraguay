---
name: python-patterns
description: Python async patterns, retry logic, structured logging, type hints, dataclasses, and common idioms
load-when: Python async/await, retry logic, structured logging, type safety in THIS codebase
not-when: FastAPI routing (use fastapi-patterns), SQL queries (use postgresql-patterns), payment logic (use payment-patterns)
project-specific: Decimal money handling, GDPR-aware logging (mask PII), Refugio domain enums
---

# Python Patterns

Load this skill when writing Python code that needs async, retry logic, logging, or type safety.

## Type Hints

### Function Signatures

```python
from typing import Optional, Union
from collections.abc import Callable, Sequence, Generator, AsyncGenerator
from datetime import datetime
from uuid import UUID


# Always annotate all parameters and return type
def find_animal(
    animal_id: UUID,
    shelter_id: UUID,
    include_deleted: bool = False,
) -> Optional["Animal"]:
    ...


# Use X | Y syntax (Python 3.10+) or Union for older
def get_donation_amount(
    amount: float | int,
    currency: str,
) -> "Money":
    ...


# Sequences: use Sequence for read-only, list for mutable
def process_animals(animals: Sequence["Animal"]) -> list["AdoptionScore"]:
    ...
```

### Type Aliases

```python
from typing import TypeAlias

# Name domain concepts
DonorId: TypeAlias = UUID
AnimalId: TypeAlias = UUID
AmountEur: TypeAlias = float

# Callable types
ValidationFn: TypeAlias = Callable[[str], bool]
```

### Dataclasses

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from uuid import UUID


@dataclass
class AdoptionRequest:
    id: UUID
    animal_id: UUID
    adopter_id: UUID
    status: str = "pending"
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    # Computed fields: use __post_init__
    def __post_init__(self) -> None:
        if self.status not in ("pending", "approved", "rejected", "completed"):
            raise ValueError(f"Invalid status: {self.status}")


# Frozen dataclasses for value objects (immutable)
@dataclass(frozen=True)
class Money:
    amount: float
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")
        if self.currency not in ("EUR", "PYG", "USD"):
            raise ValueError(f"Unsupported currency: {self.currency}")
```

---

## Async Patterns

### Basic Async

```python
import asyncio
from typing import Optional


async def get_animal_async(animal_id: str) -> Optional[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/animals/{animal_id}") as response:
            if response.status == 404:
                return None
            response.raise_for_status()
            return await response.json()


# Running multiple coroutines concurrently
async def get_multiple_animals(animal_ids: list[str]) -> list[dict]:
    tasks = [get_animal_async(aid) for aid in animal_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out errors and Nones
    return [r for r in results if isinstance(r, dict)]
```

### Async Context Manager

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator


@asynccontextmanager
async def db_transaction(conn) -> AsyncGenerator[None, None]:
    """Wrap database operations in a transaction."""
    async with conn.transaction():
        try:
            yield
        except Exception:
            # Transaction auto-rolls back on exception
            raise
```

### Async Generator

```python
from collections.abc import AsyncGenerator


async def stream_animals(shelter_id: str) -> AsyncGenerator[dict, None]:
    """Stream animals in batches — memory efficient for large shelters."""
    cursor = None
    while True:
        batch, cursor = await fetch_animal_batch(shelter_id, cursor, limit=100)
        for animal in batch:
            yield animal
        if cursor is None:
            break


# Usage
async for animal in stream_animals("shelter-uuid"):
    await process(animal)
```

---

## Retry Logic

### Simple Retry with Exponential Backoff

```python
import asyncio
import logging
from functools import wraps
from typing import TypeVar, Callable, Any

logger = logging.getLogger(__name__)
T = TypeVar("T")

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0


async def retry_async(
    fn: Callable[..., Any],
    *args: Any,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY_SECONDS,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """Retry an async function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await fn(*args, **kwargs)
        except retryable_exceptions as exc:
            if attempt == max_retries - 1:
                logger.error(
                    "Max retries exceeded",
                    extra={"function": fn.__name__, "attempts": max_retries, "error": str(exc)},
                )
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Retrying after error",
                extra={"function": fn.__name__, "attempt": attempt + 1, "delay": delay},
            )
            await asyncio.sleep(delay)

    raise RuntimeError("Unreachable")  # mypy requires this


# Usage
result = await retry_async(
    send_donation_confirmation,
    donor_id=donor.id,
    amount=amount,
    retryable_exceptions=(EmailDeliveryError, TimeoutError),
)
```

### Tenacity (library — preferred for production)

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((EmailDeliveryError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
async def send_email_with_retry(to: str, subject: str, body: str) -> None:
    await email_service.send(to=to, subject=subject, body=body)
```

---

## Structured Logging

### Logger Setup

```python
import logging
import sys
from typing import Any


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


# Module-level logger (never use root logger directly)
logger = logging.getLogger(__name__)
```

### Structured Log Messages

```python
# ✅ Log with context — searchable and filterable
logger.info(
    "Adoption request submitted",
    extra={
        "animal_id": str(animal_id),
        "adopter_id": str(adopter_id),
        "request_id": str(request.id),
    },
)

logger.warning(
    "Email delivery failed — notification not sent",
    extra={
        "donor_id": str(donor_id),
        "email": donor.email[:3] + "***",  # mask PII
        "error": str(exc),
        "attempt": attempt,
    },
)

logger.error(
    "Payment processing failed",
    extra={
        "donor_id": str(donor_id),
        "amount_eur": amount,
        "error_code": exc.code,
    },
    exc_info=True,  # includes traceback
)

# ❌ Don't log PII unmasked
logger.info(f"Processing donation from {donor.email}")  # email in logs
logger.info(f"Card ending: {card_number[-4:]}")         # any card data
```

### Contextvars for Request-Scoped Logging

```python
from contextvars import ContextVar
import uuid

request_id: ContextVar[str] = ContextVar("request_id", default="")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get("-")
        return True


# In middleware: set for each request
async def logging_middleware(request, call_next):
    token = request_id.set(str(uuid.uuid4()))
    try:
        return await call_next(request)
    finally:
        request_id.reset(token)
```

---

## Enum Patterns

```python
from enum import Enum, auto


class AnimalStatus(str, Enum):
    """Animal availability status.

    Using str mixin ensures values serialize correctly in JSON/DB.
    """
    AVAILABLE = "available"
    RESERVED = "reserved"
    ADOPTED = "adopted"
    DECEASED = "deceased"
    FOSTER = "foster"


class AdoptionRequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Return True if no further state transitions are possible."""
        return self in (self.COMPLETED, self.CANCELLED, self.REJECTED)

    def can_transition_to(self, new_status: "AdoptionRequestStatus") -> bool:
        ALLOWED = {
            self.PENDING: {self.APPROVED, self.REJECTED, self.CANCELLED},
            self.APPROVED: {self.COMPLETED, self.CANCELLED},
        }
        return new_status in ALLOWED.get(self, set())
```

---

## Context Managers

```python
from contextlib import contextmanager, suppress
from typing import Generator


@contextmanager
def timer(operation_name: str) -> Generator[None, None, None]:
    """Log execution time of a block."""
    import time
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - start
        logger.info(f"{operation_name} completed", extra={"duration_ms": round(elapsed * 1000)})


# Usage
with timer("process_adoption_batch"):
    for request in pending_requests:
        await process(request)


# suppress specific exceptions cleanly
with suppress(FileNotFoundError):
    os.remove(temp_file)
```

---

## Common Idioms

```python
# ✅ Walrus operator for assignment in condition
if match := re.search(r"\d+", text):
    number = int(match.group())

# ✅ Dictionary merge (Python 3.9+)
base_config = {"timeout": 30, "retries": 3}
override = {"timeout": 60}
config = base_config | override   # {"timeout": 60, "retries": 3}

# ✅ Unpacking in loops
donors_with_amounts = [("Alice", 100.0), ("Bob", 50.0)]
for donor_name, amount in donors_with_amounts:
    process_donation(donor_name, amount)

# ✅ Default dict for grouping
from collections import defaultdict

animals_by_status: dict[str, list[Animal]] = defaultdict(list)
for animal in all_animals:
    animals_by_status[animal.status].append(animal)

# ✅ Cached property for expensive computations
from functools import cached_property

class Shelter:
    @cached_property
    def available_count(self) -> int:
        return sum(1 for a in self.animals if a.status == "available")
```

---

## Anti-Patterns

```python
# ❌ Mutable default arguments
def add_tag(animal_id: str, tags: list[str] = []) -> None:  # shared between calls!
    tags.append(animal_id)

# ✅ Use None sentinel
def add_tag(animal_id: str, tags: list[str] | None = None) -> None:
    if tags is None:
        tags = []
    tags.append(animal_id)

# ❌ Bare except
try:
    process()
except:
    pass

# ✅ Specific exception
try:
    process()
except (ValidationError, DatabaseError) as e:
    logger.error("Processing failed", extra={"error": str(e)})
    raise

# ❌ String formatting in log calls (always evaluated even if log level disabled)
logger.debug(f"Processing {len(animals)} animals with status {status}")

# ✅ Use lazy % formatting or extra dict
logger.debug("Processing %d animals with status %s", len(animals), status)

# ❌ isinstance check on string type
if type(value) == str:

# ✅ isinstance (handles subclasses correctly)
if isinstance(value, str):
```
