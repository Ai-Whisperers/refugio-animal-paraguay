"""In-process async event bus using Python asyncio.

The EventBus dispatches DomainEvents to registered subscriber handlers.
Key properties:
  - Non-blocking: publish() returns immediately; handlers run as async tasks
  - Error isolation: one failing handler doesn't block others
  - Idempotency: duplicate events (same idempotency_key) are skipped
  - Ordering: events of the same type are processed in publish order
  - Upgradeable: interface supports future swap to Redis pub/sub

Usage:
    bus = EventBus()
    bus.subscribe("adoption.status_changed", my_handler)
    await bus.start()
    await bus.publish(event)
    await bus.stop()
"""

import asyncio
import contextlib
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from src.events.types import DomainEvent, EventType

logger = logging.getLogger(__name__)

# Type alias for event handler: an async callable that takes a DomainEvent
EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]

# Maximum number of unprocessed events per queue before applying backpressure
MAX_QUEUE_SIZE = 1000


class EventBus:
    """In-process async event dispatcher.

    Maintains one asyncio.Queue per event type. A dedicated consumer task
    per event type reads events and dispatches them to all subscribers.
    """

    def __init__(self, max_queue_size: int = MAX_QUEUE_SIZE) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._queues: dict[str, asyncio.Queue[DomainEvent]] = {}
        self._consumer_tasks: dict[str, asyncio.Task[None]] = {}
        self._processed_keys: set[str] = set()
        self._max_queue_size = max_queue_size
        self._running = False

    def subscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        """Register a handler for an event type.

        Args:
            event_type: The event type to subscribe to (EventType enum or string).
            handler: Async callable that receives a DomainEvent.
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._subscribers[key].append(handler)
        logger.info(
            "Subscriber registered: %s -> %s",
            key,
            getattr(handler, "__qualname__", repr(handler)),
        )

    def unsubscribe(self, event_type: EventType | str, handler: EventHandler) -> None:
        """Remove a handler from an event type.

        Args:
            event_type: The event type to unsubscribe from.
            handler: The handler to remove.
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type
        handlers = self._subscribers.get(key, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.info(
                "Subscriber removed: %s -> %s",
                key,
                getattr(handler, "__qualname__", repr(handler)),
            )

    async def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to the bus.

        The event is placed on the appropriate queue for async processing.
        Returns immediately (non-blocking).

        Args:
            event: The domain event to publish.

        Raises:
            RuntimeError: If the bus has not been started.
        """
        if not self._running:
            raise RuntimeError(
                "EventBus is not running. Call start() before publishing events."
            )

        key = event.event_type.value

        # Skip if no subscribers for this event type
        if key not in self._subscribers or not self._subscribers[key]:
            logger.debug("No subscribers for event type %s, skipping", key)
            return

        # Idempotency check
        idem_key = str(event.idempotency_key)
        if idem_key in self._processed_keys:
            logger.warning(
                "Duplicate event skipped: idempotency_key=%s, event_type=%s",
                idem_key,
                key,
            )
            return

        # Ensure queue exists for this event type
        if key not in self._queues:
            self._queues[key] = asyncio.Queue(maxsize=self._max_queue_size)
            self._consumer_tasks[key] = asyncio.create_task(
                self._consume(key),
                name=f"event-consumer-{key}",
            )

        await self._queues[key].put(event)
        logger.debug("Event published: %s (id=%s)", key, event.id)

    async def _consume(self, event_type_key: str) -> None:
        """Consumer loop for a single event type queue.

        Reads events from the queue and dispatches to all subscribers.
        Runs until the bus is stopped.
        """
        queue = self._queues[event_type_key]
        while self._running or not queue.empty():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.5)
            except TimeoutError:
                continue

            # Idempotency check (re-check in consumer in case of race)
            idem_key = str(event.idempotency_key)
            if idem_key in self._processed_keys:
                queue.task_done()
                continue

            self._processed_keys.add(idem_key)

            handlers = self._subscribers.get(event_type_key, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception:
                    logger.exception(
                        "Event handler %s failed for event %s (id=%s). "
                        "Continuing to next handler.",
                        getattr(handler, "__qualname__", repr(handler)),
                        event_type_key,
                        event.id,
                    )

            queue.task_done()

    async def start(self) -> None:
        """Start the event bus. Must be called before publishing events."""
        if self._running:
            return
        self._running = True
        self._processed_keys.clear()
        logger.info("EventBus started")

    async def stop(self) -> None:
        """Stop the event bus gracefully.

        Waits for all queued events to be processed, then cancels consumer tasks.
        """
        if not self._running:
            return

        self._running = False

        # Wait for all queues to drain
        for key, queue in self._queues.items():
            try:
                await asyncio.wait_for(queue.join(), timeout=5.0)
            except TimeoutError:
                logger.warning(
                    "Timeout waiting for event queue %s to drain. "
                    "%d events may be lost.",
                    key,
                    queue.qsize(),
                )

        # Cancel consumer tasks
        for task in self._consumer_tasks.values():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        self._queues.clear()
        self._consumer_tasks.clear()
        logger.info("EventBus stopped")

    @property
    def is_running(self) -> bool:
        """Whether the event bus is currently running."""
        return self._running

    @property
    def subscriber_count(self) -> int:
        """Total number of registered handler subscriptions."""
        return sum(len(handlers) for handlers in self._subscribers.values())

    def get_handlers(self, event_type: EventType | str) -> list[EventHandler]:
        """Return the list of handlers registered for an event type."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        return list(self._subscribers.get(key, []))
