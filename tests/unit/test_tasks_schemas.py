"""Unit tests for task model enums, constants, and API schemas (RAP-185)."""

from datetime import UTC

import pytest
from pydantic import ValidationError
from src.api.tasks import TaskCreateRequest, TaskUpdateRequest
from src.db.models.task import (
    VALID_TASK_CATEGORIES,
    VALID_TASK_PRIORITIES,
    VALID_TASK_STATUSES,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)


class TestTaskStatusEnum:
    def test_all_expected_values_present(self) -> None:
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_valid_statuses_set(self) -> None:
        assert {"pending", "in_progress", "completed", "cancelled"} == VALID_TASK_STATUSES

    def test_enum_is_str(self) -> None:
        assert isinstance(TaskStatus.PENDING, str)


class TestTaskCategoryEnum:
    def test_all_expected_values_present(self) -> None:
        assert TaskCategory.FEEDING == "feeding"
        assert TaskCategory.CLEANING == "cleaning"
        assert TaskCategory.WALKING == "walking"
        assert TaskCategory.SOCIALIZATION == "socialization"
        assert TaskCategory.VETERINARY_ASSISTANCE == "veterinary_assistance"
        assert TaskCategory.TRANSPORT == "transport"
        assert TaskCategory.ADMIN == "admin"
        assert TaskCategory.OTHER == "other"

    def test_valid_categories_set(self) -> None:
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
        assert expected == VALID_TASK_CATEGORIES

    def test_enum_is_str(self) -> None:
        assert isinstance(TaskCategory.FEEDING, str)


class TestTaskPriorityEnum:
    def test_all_expected_values_present(self) -> None:
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.URGENT == "urgent"

    def test_valid_priorities_set(self) -> None:
        assert {"low", "medium", "high", "urgent"} == VALID_TASK_PRIORITIES

    def test_enum_is_str(self) -> None:
        assert isinstance(TaskPriority.URGENT, str)


class TestTaskCreateRequest:
    def test_minimal_valid_request(self) -> None:
        req = TaskCreateRequest(title="Feed the dogs")
        assert req.title == "Feed the dogs"
        assert req.category == TaskCategory.OTHER
        assert req.priority == TaskPriority.MEDIUM
        assert req.assigned_to is None
        assert req.due_date is None
        assert req.animal_id is None

    def test_full_valid_request(self) -> None:
        from datetime import datetime
        from uuid import uuid4

        user_id = uuid4()
        animal_id = uuid4()
        due = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)

        req = TaskCreateRequest(
            title="Morning feeding round",
            description="Feed all dogs in kennel A",
            category=TaskCategory.FEEDING,
            priority=TaskPriority.HIGH,
            assigned_to=user_id,
            due_date=due,
            animal_id=animal_id,
        )
        assert req.title == "Morning feeding round"
        assert req.category == TaskCategory.FEEDING
        assert req.priority == TaskPriority.HIGH
        assert req.assigned_to == user_id
        assert req.due_date == due
        assert req.animal_id == animal_id

    def test_title_too_long_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            TaskCreateRequest(title="x" * 201)
        errors = exc_info.value.errors()
        assert any("title" in str(e["loc"]) for e in errors)

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreateRequest(title="Test", category="invalid_category")

    def test_invalid_priority_raises(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreateRequest(title="Test", priority="super_urgent")

    def test_empty_title_raises(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreateRequest(title="")


class TestTaskUpdateRequest:
    def test_empty_update_is_valid(self) -> None:
        req = TaskUpdateRequest()
        assert req.title is None
        assert req.status is None
        assert req.category is None

    def test_status_update_only(self) -> None:
        req = TaskUpdateRequest(status=TaskStatus.COMPLETED)
        assert req.status == TaskStatus.COMPLETED
        assert req.title is None

    def test_completion_notes_max_length(self) -> None:
        req = TaskUpdateRequest(completion_notes="x" * 2000)
        assert req.completion_notes is not None
        assert len(req.completion_notes) == 2000

    def test_completion_notes_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            TaskUpdateRequest(completion_notes="x" * 2001)

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValidationError):
            TaskUpdateRequest(status="done")
