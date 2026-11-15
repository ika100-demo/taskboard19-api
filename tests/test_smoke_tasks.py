"""Smoke tests for spec 001 (AC-001.1, AC-001.5). Base URL only; own data is `smoke-<uuid>`."""

from __future__ import annotations

import uuid
from datetime import datetime

import httpx
import pytest


@pytest.mark.smoke
@pytest.mark.writes
def test_smoke_create_task(smoke_base_url: str) -> None:  # AC-001.1
    title = f"smoke-{uuid.uuid4()}"
    response = httpx.post(
        smoke_base_url + "/tasks", json={"title": title, "due_date": "2026-12-01"}, timeout=10
    )
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["id"] > 0
    assert body["title"] == title
    assert body["due_date"] == "2026-12-01"
    assert body["created_at"].endswith("Z")
    datetime.fromisoformat(body["created_at"][:-1] + "+00:00")


@pytest.mark.smoke
def test_smoke_create_task_rejects_empty_title(smoke_base_url: str) -> None:  # AC-001.1
    response = httpx.post(smoke_base_url + "/tasks", json={"title": ""}, timeout=10)
    assert response.status_code == 422
    assert ["body", "title"] in [e["loc"] for e in response.json()["detail"]]


@pytest.mark.smoke
def test_smoke_list_tasks_is_json_array(smoke_base_url: str) -> None:  # AC-001.5
    response = httpx.get(smoke_base_url + "/tasks", timeout=10)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    for task in body:
        assert {"id", "title", "due_date", "created_at"} <= set(task)


@pytest.mark.smoke
@pytest.mark.writes
def test_smoke_list_tasks_in_creation_order(smoke_base_url: str) -> None:  # AC-001.5
    created = []
    for _ in range(3):
        response = httpx.post(
            smoke_base_url + "/tasks", json={"title": f"smoke-{uuid.uuid4()}"}, timeout=10
        )
        assert response.status_code == 201
        created.append(response.json())
    listing = httpx.get(smoke_base_url + "/tasks", timeout=10)
    assert listing.status_code == 200
    body = listing.json()
    ids = [t["id"] for t in created]
    mine = [t for t in body if t["id"] in ids]
    assert mine == created
