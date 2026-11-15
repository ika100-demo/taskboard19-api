"""Acceptance tests for spec 001: create and list tasks in memory."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from taskboard19_api.main import app


def _locs(response: Any) -> list[list[Any]]:
    return [entry["loc"] for entry in response.json()["detail"]]


def _assert_utc_timestamp(value: str) -> None:
    assert isinstance(value, str)
    assert value.endswith("Z")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    assert parsed.utcoffset() == timedelta(0)
    assert abs(datetime.now(UTC) - parsed) < timedelta(minutes=5)


def test_create_task_with_title_and_due_date() -> None:  # AC-001.1
    with TestClient(app) as client:
        response = client.post("/tasks", json={"title": "Buy milk", "due_date": "2026-12-01"})
        assert response.status_code == 201
        body = response.json()
        assert isinstance(body["id"], int)
        assert not isinstance(body["id"], bool)
        assert body["id"] > 0
        assert body["title"] == "Buy milk"
        assert body["due_date"] == "2026-12-01"
        _assert_utc_timestamp(body["created_at"])


def test_create_task_without_due_date() -> None:  # AC-001.2
    with TestClient(app) as client:
        response = client.post("/tasks", json={"title": "Call Bob"})
        assert response.status_code == 201
        assert response.json()["title"] == "Call Bob"
        assert response.json()["due_date"] is None


def test_create_task_with_null_due_date() -> None:  # AC-001.2
    with TestClient(app) as client:
        response = client.post("/tasks", json={"title": "Call Bob", "due_date": None})
        assert response.status_code == 201
        assert response.json()["due_date"] is None


def test_title_200_chars_accepted() -> None:  # AC-001.3
    with TestClient(app) as client:
        title = "x" * 200
        response = client.post("/tasks", json={"title": title})
        assert response.status_code == 201
        assert response.json()["title"] == title


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"due_date": "2026-12-01"},
        {"title": 42},
        {"title": None},
        {"title": ["a"]},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
    ],
    ids=["missing", "missing-with-date", "int", "null", "list", "empty", "whitespace", "too-long"],
)
def test_invalid_title_rejected(payload: dict[str, Any]) -> None:  # AC-001.3
    with TestClient(app) as client:
        response = client.post("/tasks", json=payload)
        assert response.status_code == 422
        assert ["body", "title"] in _locs(response)
        listing = client.get("/tasks")
        assert listing.status_code == 200
        assert listing.json() == []


@pytest.mark.parametrize(
    "due_date",
    ["tomorrow", "2026-13-01", "2026-12-01T10:00:00", 20261201, ""],
    ids=["word", "bad-month", "datetime", "integer", "empty"],
)
def test_invalid_due_date_rejected(due_date: Any) -> None:  # AC-001.4
    with TestClient(app) as client:
        response = client.post("/tasks", json={"title": "Buy milk", "due_date": due_date})
        assert response.status_code == 422
        assert ["body", "due_date"] in _locs(response)
        listing = client.get("/tasks")
        assert listing.status_code == 200
        assert listing.json() == []


def test_list_returns_tasks_in_creation_order() -> None:  # AC-001.5
    with TestClient(app) as client:
        created = []
        for title in ("A", "B", "C"):
            response = client.post("/tasks", json={"title": title})
            assert response.status_code == 201
            created.append(response.json())
        listing = client.get("/tasks")
        assert listing.status_code == 200
        body = listing.json()
        assert [t["title"] for t in body] == ["A", "B", "C"]
        assert body == created
        assert [t["id"] for t in body] == sorted(t["id"] for t in body)
        assert len({t["id"] for t in body}) == 3


def test_list_is_empty_initially() -> None:  # AC-001.6
    with TestClient(app) as client:
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []


def test_restart_empties_list_and_resets_ids() -> None:  # AC-001.7
    with TestClient(app) as client:
        assert client.post("/tasks", json={"title": "one"}).status_code == 201
        assert client.post("/tasks", json={"title": "two"}).status_code == 201
        assert len(client.get("/tasks").json()) == 2
    with TestClient(app) as client:
        response = client.get("/tasks")
        assert response.status_code == 200
        assert response.json() == []
        created = client.post("/tasks", json={"title": "again"})
        assert created.status_code == 201
        assert created.json()["id"] == 1
