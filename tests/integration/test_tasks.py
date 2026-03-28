"""Integration tests for task assignment and tracking API (RAP-185).

Requires a running PostgreSQL instance (refugio_dev) with tasks table created.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.config import Settings
from src.db.session import init_engine

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_tasks() -> None:  # type: ignore[return]
    """Delete all tasks after each test to keep tests isolated."""
    yield
    settings = Settings()
    engine = init_engine(settings)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text("DELETE FROM tasks"))
        await session.commit()
    await engine.dispose()


# ---------------------------------------------------------------------------
# GET /api/tasks/categories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_task_categories(client: AsyncClient) -> None:
    """Categories endpoint returns all valid task categories."""
    resp = await client.get("/api/tasks/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    expected = {
        "feeding",
        "cleaning",
        "walking",
        "socialization",
        "veterinary_assistance",
        "transport",
        "admin",
        "other",
    }
    assert set(data["categories"]) == expected


# ---------------------------------------------------------------------------
# GET /api/tasks/priorities
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_task_priorities(client: AsyncClient) -> None:
    """Priorities endpoint returns all valid task priorities."""
    resp = await client.get("/api/tasks/priorities")
    assert resp.status_code == 200
    data = resp.json()
    assert "priorities" in data
    assert set(data["priorities"]) == {"low", "medium", "high", "urgent"}


# ---------------------------------------------------------------------------
# POST /api/tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_minimal_task(client: AsyncClient) -> None:
    """Staff can create a task with just a title."""
    resp = await client.post("/api/tasks", json={"title": "Morning feeding"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Morning feeding"
    assert data["status"] == "pending"
    assert data["category"] == "other"
    assert data["priority"] == "medium"
    assert data["assigned_to"] is None
    assert "id" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_with_all_fields(client: AsyncClient) -> None:
    """Staff can create a fully specified task."""
    resp = await client.post(
        "/api/tasks",
        json={
            "title": "Clean kennel A",
            "description": "Thorough cleaning including disinfection",
            "category": "cleaning",
            "priority": "high",
            "due_date": "2026-04-01T09:00:00Z",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Clean kennel A"
    assert data["category"] == "cleaning"
    assert data["priority"] == "high"
    assert data["description"] == "Thorough cleaning including disinfection"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_title_required(client: AsyncClient) -> None:
    """Creating a task without a title returns 422."""
    resp = await client.post("/api/tasks", json={"category": "feeding"})
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_invalid_category(client: AsyncClient) -> None:
    """Creating a task with an invalid category returns 422."""
    resp = await client.post("/api/tasks", json={"title": "Test", "category": "invalid"})
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_task_invalid_priority(client: AsyncClient) -> None:
    """Creating a task with an invalid priority returns 422."""
    resp = await client.post("/api/tasks", json={"title": "Test", "priority": "super_high"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/tasks/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_existing_task(client: AsyncClient) -> None:
    """Get a specific task by ID."""
    create_resp = await client.post(
        "/api/tasks", json={"title": "Walk the dogs", "category": "walking"}
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task_id
    assert get_resp.json()["title"] == "Walk the dogs"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_nonexistent_task_returns_404(client: AsyncClient) -> None:
    """Getting a non-existent task returns 404."""
    resp = await client.get(f"/api/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_empty(client: AsyncClient) -> None:
    """Empty list returns total 0."""
    resp = await client.get("/api/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_after_create(client: AsyncClient) -> None:
    """Created tasks appear in the list."""
    await client.post("/api/tasks", json={"title": "Task A", "category": "feeding"})
    await client.post("/api/tasks", json={"title": "Task B", "category": "cleaning"})

    resp = await client.get("/api/tasks")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_filter_by_category(client: AsyncClient) -> None:
    """Category filter narrows results correctly."""
    await client.post("/api/tasks", json={"title": "Feed dogs", "category": "feeding"})
    await client.post("/api/tasks", json={"title": "Clean kennel", "category": "cleaning"})

    resp = await client.get("/api/tasks?category=feeding")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "feeding"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_filter_by_invalid_status_returns_422(client: AsyncClient) -> None:
    """Invalid status filter returns 422."""
    resp = await client.get("/api/tasks?task_status=invalid_status")
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_tasks_pagination(client: AsyncClient) -> None:
    """Pagination returns the correct subset."""
    for i in range(5):
        await client.post("/api/tasks", json={"title": f"Task {i}"})

    resp = await client.get("/api/tasks?page=1&page_size=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5


# ---------------------------------------------------------------------------
# PATCH /api/tasks/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_title(client: AsyncClient) -> None:
    """Staff can update a task's title."""
    create_resp = await client.post("/api/tasks", json={"title": "Old title"})
    task_id = create_resp.json()["id"]

    update_resp = await client.patch(f"/api/tasks/{task_id}", json={"title": "New title"})
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "New title"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_status_to_completed(client: AsyncClient) -> None:
    """Completing a task sets completed_at automatically."""
    create_resp = await client.post("/api/tasks", json={"title": "Finish me"})
    task_id = create_resp.json()["id"]

    update_resp = await client.patch(
        f"/api/tasks/{task_id}",
        json={"status": "completed", "completion_notes": "All done!"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["status"] == "completed"
    assert data["completion_notes"] == "All done!"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_task_priority(client: AsyncClient) -> None:
    """Staff can escalate a task's priority."""
    create_resp = await client.post("/api/tasks", json={"title": "Urgent task"})
    task_id = create_resp.json()["id"]

    update_resp = await client.patch(f"/api/tasks/{task_id}", json={"priority": "urgent"})
    assert update_resp.status_code == 200
    assert update_resp.json()["priority"] == "urgent"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_nonexistent_task_returns_404(client: AsyncClient) -> None:
    """Updating a non-existent task returns 404."""
    resp = await client.patch(f"/api/tasks/{uuid.uuid4()}", json={"title": "Ghost"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/tasks/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_task(client: AsyncClient) -> None:
    """Staff can delete a task; it disappears from GET after deletion."""
    create_resp = await client.post("/api/tasks", json={"title": "Deletable task"})
    task_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/tasks/{task_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/tasks/{task_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_nonexistent_task_returns_404(client: AsyncClient) -> None:
    """Deleting a non-existent task returns 404."""
    resp = await client.delete(f"/api/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404
