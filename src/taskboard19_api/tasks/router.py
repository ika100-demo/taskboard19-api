"""HTTP routes for tasks: create and list (spec 001)."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request

from taskboard19_api.tasks.models import Task, TaskCreate
from taskboard19_api.tasks.store import TaskStore

router = APIRouter(tags=["tasks"])
log = structlog.get_logger()


def get_task_store(request: Request) -> TaskStore:
    """Return the live task store held on the app state."""
    store: TaskStore = request.app.state.task_store
    return store


StoreDep = Annotated[TaskStore, Depends(get_task_store)]


@router.post("/tasks", status_code=201, response_model=Task)
def create_task(body: TaskCreate, store: StoreDep) -> Task:
    """Create a task; the title is never logged to keep user content out of logs."""
    task = store.create(body.title, body.due_date)
    log.info("task_created", task_id=task.id)
    return task


@router.get("/tasks", response_model=list[Task])
def list_tasks(store: StoreDep) -> list[Task]:
    """Return every task in creation order."""
    return store.list()
