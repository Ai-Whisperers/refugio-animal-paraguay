"""FastAPI application factory and lifespan.

Entry point for the Refugio Animal Paraguay API. Creates the FastAPI app,
registers routers, configures CORS/rate limiting/error handling, and manages
the database engine lifecycle via lifespan.

Run locally:
    uvicorn src.app:app --reload
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api.admin import router as admin_router
from src.api.adopters import router as adopters_router
from src.api.adoption_requests import router as adoption_requests_router
from src.api.animals import router as animals_router
from src.api.auth import router as auth_router
from src.api.donations import router as donations_router
from src.api.donors import router as donors_router
from src.api.health import router as health_router
from src.api.in_kind_donations import router as in_kind_donations_router
from src.api.public import router as public_router
from src.audit.middleware import AuditMiddleware
from src.config import Settings, get_settings
from src.db.session import dispose_engine, init_engine
from src.events.bus import EventBus
from src.middleware.error_handler import register_exception_handlers
from src.middleware.rate_limiter import configure_limiter, limiter
from src.middleware.request_id import RequestIDMiddleware
from src.notifications.handlers import NotificationHandlers
from src.notifications.service import EmailService
from src.notifications.templates import TemplateRenderer


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: DB engine + event bus on startup/shutdown."""
    settings: Settings = get_settings()
    init_engine(settings)

    # Start the event bus and attach to app state for handler access
    event_bus = EventBus()
    application.state.event_bus = event_bus
    await event_bus.start()

    # Register email notification handlers on the event bus
    email_service = EmailService(settings)
    renderer = TemplateRenderer()
    notification_handlers = NotificationHandlers(email_service, renderer)
    notification_handlers.register(event_bus)

    yield

    await event_bus.stop()
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # --- Request ID middleware (must be outermost to cover all responses) ---
    application.add_middleware(RequestIDMiddleware)

    # --- Audit trail middleware (after auth, records successful write ops) ---
    application.add_middleware(AuditMiddleware)

    # --- CORS middleware ---
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rate limiting ---
    configure_limiter(enabled=settings.rate_limit_enabled)
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- Exception handlers (overrides default FastAPI handlers) ---
    register_exception_handlers(application)

    # --- Routers ---
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(animals_router)
    application.include_router(adopters_router)
    application.include_router(adoption_requests_router)
    application.include_router(donors_router)
    application.include_router(donations_router)
    application.include_router(in_kind_donations_router)
    application.include_router(admin_router)
    application.include_router(public_router)

    return application


# Module-level app instance — used by uvicorn and test client
app = create_app()
