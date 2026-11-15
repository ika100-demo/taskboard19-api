"""Unit tests for task models."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from taskboard19_api.tasks.models import Task, TaskCreate


def _locs(exc: ValidationError) -> list[tuple[Any, ...]]:
    return [e["loc"] for e in exc.errors()]


def test_valid_create() -> None:
    task = TaskCreate.model_validate({"title": " Buy milk ", "due_date": "2026-12-01"})
    assert task.title == " Buy milk "
    assert task.due_date == date(2026, 12, 1)


def test_due_date_optional() -> None:
    assert TaskCreate.model_validate({"title": "x"}).due_date is None
    assert TaskCreate.model_validate({"title": "x", "due_date": None}).due_date is None


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": 5},
        {"title": ""},
        {"title": "   "},
        {"title": "a" * 201},
    ],
)
def test_invalid_title(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError) as exc:
        TaskCreate.model_validate(payload)
    assert _locs(exc.value) == [("title",)]


def test_title_200_ok() -> None:
    assert len(TaskCreate.model_validate({"title": "a" * 200}).title) == 200


@pytest.mark.parametrize("value", ["tomorrow", "2026-13-01", "2026-12-01T10:00:00", 20261201])
def test_invalid_due_date(value: Any) -> None:
    with pytest.raises(ValidationError) as exc:
        TaskCreate.model_validate({"title": "x", "due_date": value})
    assert _locs(exc.value) == [("due_date",)]


def test_task_serializes_utc_with_z() -> None:
    task = Task(id=1, title="x", due_date=None, created_at=datetime.now(UTC))
    assert task.model_dump(mode="json")["created_at"].endswith("Z")
