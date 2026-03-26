"""Integration tests for GET /health endpoint.

These tests use httpx.AsyncClient against the real FastAPI app.
The happy-path test requires a running PostgreSQL instance (refugio_dev).
Run only integration tests: pytest -m integration tests/integration/
"""

import pytest
from httpx import ASGITransport, AsyncClient
from src.app import app
from src.config import Settings
from src.db.session import init_engine


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_returns_ok_when_db_reachable(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "connected"


@pytest.mark.asyncio
async def test_health_returns_503_when_db_unreachable() -> None:
    """Simulate DB failure by patching the session execute call."""
    settings = Settings(database_url="postgresql+asyncpg://bad:creds@127.0.0.1:9999/nonexistent")
    init_engine(settings)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "unreachable"
