"""Thread-safe in-memory task store (spec 001)."""

from __future__ import annotations

import threading
from datetime import UTC, date, datetime

from taskboard19_api.tasks.models import Task


class TaskStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: list[Task] = []
        self._next_id = 1

    def create(self, title: str, due_date: date | None) -> Task:
        with self._lock:
            task = Task(
                id=self._next_id,
                title=title,
                due_date=due_date,
                created_at=datetime.now(UTC),
            )
            self._tasks.append(task)
            self._next_id += 1
            return task

    def list(self) -> list[Task]:
        with self._lock:
            return list(self._tasks)

    def clear(self) -> None:
        with self._lock:
            self._tasks = []
            self._next_id = 1
