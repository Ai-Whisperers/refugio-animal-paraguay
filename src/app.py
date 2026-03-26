"""FastAPI application factory and lifespan.

Entry point for the Refugio Animal Paraguay API. Creates the FastAPI app,
registers routers, configures middleware (CORS, rate limiting, request ID),
and manages the database engine lifecycle via lifespan.

Run locally:
    uvicorn src.app:app --reload
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.adopters import router as adopters_router
from src.api.adoption_requests import router as adoption_requests_router
from src.api.animals import router as animals_router
from src.api.auth import router as auth_router
from src.api.donations import router as donations_router
from src.api.donors import router as donors_router
from src.api.health import router as health_router
from src.config import Settings, get_settings
from src.db.session import dispose_engine, init_engine
from src.middleware.error_handler import register_error_handlers
from src.middleware.rate_limit import limiter
from src.middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: open DB engine on startup, close on shutdown."""
    settings: Settings = get_settings()
    init_engine(settings)
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    # -- Middleware (order matters: outermost first) --

    # Request ID — outermost so every response gets an ID, even errors.
    app.add_middleware(RequestIDMiddleware)

    # CORS — must be added before route registration is finalized.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
    )

    # Rate limiting
    app.state.limiter = limiter
    if not settings.rate_limit_enabled:
        limiter.enabled = False

    # -- Error handlers --
    register_error_handlers(app)

    # -- Routers --
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(animals_router)
    app.include_router(adopters_router)
    app.include_router(adoption_requests_router)
    app.include_router(donors_router)
    app.include_router(donations_router)

    return app


# Module-level app instance — used by uvicorn and test client
app = create_app()
