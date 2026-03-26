"""Event bus core: base event schema and async dispatcher.

The EventBus provides a simple publish/subscribe mechanism using asyncio.
Handlers are called concurrently with error isolation — one failing handler
does not block others.

Design decisions:
- Dataclasses (not Pydantic) for lightweight internal events
- asyncio.create_task for fire-and-forget delivery
- Per-handler error isolation with configurable retry
- Module-level singleton for app-wide access
"""

import asyncio
import contextlib
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Type alias for async event handlers
EventHandler = Callable[["DomainEvent"], Coroutine[Any, Any, None]]

MAX_HANDLER_RETRIES = 2
RETRY_DELAY_SECONDS = 0.1


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    All events carry standard metadata for tracing and deduplication.
    Subclasses add domain-specific payload fields.

    Attributes:
        event_type: Dot-notation identifier (e.g., "adoption.status_changed").
        payload: Domain-specific data as a plain dict.
        timestamp: UTC datetime when the event was created.
        actor_id: UUID string of the user/system that triggered the event, or None.
        idempotency_key: Unique key to prevent duplicate processing.
    """

    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    actor_id: str | None = None
    idempotency_key: str = field(default_factory=lambda: str(uuid.uuid4()))


class EventBus:
    """In-process async event dispatcher.

    Usage:
        bus = EventBus()

        async def on_adoption(event: DomainEvent) -> None:
            print(f"Adoption changed: {event.payload}")

        bus.subscribe("adoption.status_changed", on_adoption)
        await bus.publish(AdoptionStatusChanged(payload={...}))

    Error isolation: if a handler raises, the error is logged but other
    handlers for the same event type still execute.
    """

    def __init__(self, max_retries: int = MAX_HANDLER_RETRIES) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._max_retries = max_retries

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for an event type.

        Multiple handlers can subscribe to the same event type.
        Handlers are called in registration order.
        """
        self._handlers[event_type].append(handler)
        handler_name = getattr(handler, "__qualname__", repr(handler))
        logger.debug(
            "Subscribed %s to event type '%s'",
            handler_name,
            event_type,
        )

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type. No-op if not subscribed."""
        handlers = self._handlers.get(event_type, [])
        with contextlib.suppress(ValueError):
            handlers.remove(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all registered handlers.

        Handlers are dispatched concurrently. Each handler runs in its own
        task with error isolation — a failing handler does not prevent other
        handlers from executing.
        """
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug(
                "No handlers for event type '%s' (idempotency_key=%s)",
                event.event_type,
                event.idempotency_key,
            )
            return

        logger.info(
            "Publishing '%s' to %d handler(s) (idempotency_key=%s)",
            event.event_type,
            len(handlers),
            event.idempotency_key,
        )

        tasks = [asyncio.create_task(self._invoke_handler(handler, event)) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _invoke_handler(self, handler: EventHandler, event: DomainEvent) -> None:
        """Invoke a single handler with retry logic and error isolation."""
        last_error: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                await handler(event)
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Handler %s failed on attempt %d/%d for '%s': %s",
                    getattr(handler, "__qualname__", repr(handler)),
                    attempt,
                    self._max_retries,
                    event.event_type,
                    exc,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)

        # All retries exhausted
        logger.error(
            "Handler %s permanently failed for '%s' after %d attempts: %s",
            getattr(handler, "__qualname__", repr(handler)),
            event.event_type,
            self._max_retries,
            last_error,
        )

    def clear(self) -> None:
        """Remove all registered handlers. Useful for testing."""
        self._handlers.clear()

    @property
    def handler_count(self) -> int:
        """Total number of registered handler registrations."""
        return sum(len(h) for h in self._handlers.values())


# Module-level singleton — import and use throughout the app
event_bus = EventBus()
