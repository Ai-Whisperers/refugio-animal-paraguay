"""FastAPI dependency for accessing the event bus.

Usage in route handlers:
    @router.post("/something")
    async def create_thing(
        event_bus: EventBus = Depends(get_event_bus),
    ) -> ...:
        await event_bus.publish(some_event)
"""

from fastapi import Request

from src.events.bus import EventBus


def get_event_bus(request: Request) -> EventBus:
    """Extract the EventBus instance from application state.

    The EventBus is attached during app lifespan startup.

    Raises:
        RuntimeError: If the event bus is not available in app state.
    """
    event_bus: EventBus | None = getattr(request.app.state, "event_bus", None)
    if event_bus is None:
        raise RuntimeError("EventBus not available. Ensure the app lifespan has started.")
    return event_bus
