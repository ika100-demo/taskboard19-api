"""Unit tests for TaskStore."""

from __future__ import annotations

from datetime import date

from taskboard19_api.tasks import TaskStore


def test_ids_sequential_from_one() -> None:
    store = TaskStore()
    assert [store.create("t", None).id for _ in range(3)] == [1, 2, 3]


def test_creation_order_and_fields() -> None:
    store = TaskStore()
    store.create("A", date(2026, 12, 1))
    store.create("B", None)
    tasks = store.list()
    assert [t.title for t in tasks] == ["A", "B"]
    assert tasks[0].due_date == date(2026, 12, 1)
    assert tasks[1].due_date is None


def test_list_returns_copy() -> None:
    store = TaskStore()
    store.create("A", None)
    store.list().clear()
    assert len(store.list()) == 1


def test_clear_resets_counter() -> None:
    store = TaskStore()
    store.create("A", None)
    store.clear()
    assert store.list() == []
    assert store.create("B", None).id == 1
