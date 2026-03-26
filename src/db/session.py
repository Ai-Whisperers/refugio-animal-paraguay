"""Async SQLAlchemy engine and session factory.

Usage in FastAPI route handlers:
    async def my_route(db: AsyncSession = Depends(get_db)) -> ...:
        result = await db.execute(select(Animal))

The engine is created lazily on first call to get_engine() and cached for
the lifetime of the process. Call dispose_engine() during app shutdown.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config import Settings

# Module-level singleton — set during app startup via init_engine()
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings) -> AsyncEngine:
    """Create and cache the async SQLAlchemy engine.

    Must be called once during application startup (inside FastAPI lifespan).
    Subsequent calls to get_db() will reuse the cached engine.
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        str(settings.database_url),
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine


async def dispose_engine() -> None:
    """Close all connections in the engine pool.

    Must be called during application shutdown (inside FastAPI lifespan).
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def get_session_factory() -> async_sessionmaker[AsyncSession] | None:
    """Return the module-level session factory, or None if not initialised.

    Used by components that need to create their own sessions outside
    the request lifecycle (e.g., event bus handlers).
    """
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yield an AsyncSession per request.

    Commits on success; rolls back on any exception.
    """
    if _session_factory is None:
        raise RuntimeError("Database engine not initialised. Call init_engine() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
