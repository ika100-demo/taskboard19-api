---
spec_id: 001-create-and-list-tasks-in-memory
shape: service-python
spec_hash: e7b0847fc172
summary: In-memory task resource with POST /tasks (validated) and GET /tasks in creation order
tasks:
  - id: t1
    title: Add task models and in-memory TaskStore
    files: [src/taskboard19_api/tasks/__init__.py, src/taskboard19_api/tasks/models.py, src/taskboard19_api/tasks/store.py, tests/test_task_store.py, tests/test_task_models.py]
    covers: [AC-001.1, AC-001.2, AC-001.3, AC-001.4, AC-001.5, AC-001.6, AC-001.7]
    parallel_safe: true
    depends_on: []
    done: true
  - id: t2
    title: Expose POST /tasks and GET /tasks and wire the store into the app
    files: [src/taskboard19_api/tasks/router.py, src/taskboard19_api/tasks/__init__.py, src/taskboard19_api/main.py]
    covers: [AC-001.1, AC-001.2, AC-001.3, AC-001.4, AC-001.5, AC-001.6, AC-001.7]
    parallel_safe: false
    depends_on: [t1]
    done: true
---

# Plan — 001 Create and list tasks in memory

Contract and interfaces: [design.md](design.md).

## t1 — Add task models and in-memory TaskStore

**Files:** src/taskboard19_api/tasks/__init__.py, src/taskboard19_api/tasks/models.py, src/taskboard19_api/tasks/store.py, tests/test_task_store.py, tests/test_task_models.py
**Covers:** AC-001.1, AC-001.2, AC-001.3, AC-001.4, AC-001.5, AC-001.6, AC-001.7
**Goal:** Provide the request/response models with the spec's validation rules, plus a thread-safe in-memory store that assigns sequential ids and keeps creation order. The HTTP layer in t2 then only wires them up.

**Implementation notes:**
- `TaskCreate.title`: `StrictStr`, `min_length=1`, `max_length=200`, plus an after-validator that rejects strings with no non-whitespace character. Never strip; store as sent.
- `TaskCreate.due_date`: `date | None = None` with a `mode="before"` validator. Pass `None` through. Anything that is not a `str` matching `^\d{4}-\d{2}-\d{2}$` raises `ValueError`. Then `date.fromisoformat` (an invalid date such as `2026-13-01` raises).
- `Task`: `id: int`, `title: str`, `due_date: date | None`, `created_at: datetime` (aware UTC). Pydantic v2 serializes it with a `Z` suffix; confirm that in a unit test.
- `TaskStore`: `create`, `list` (returns a copy), `clear`, all guarded by one `threading.Lock`. Ids start at 1 and increase by 1. `created_at = datetime.now(UTC)`.
- `tasks/__init__.py` exports `TaskStore` (t2 adds `router`).
- Unit tests: id sequence, order, list copy isolation, clear resets the counter, and every invalid title/due_date case from AC-001.3/AC-001.4 raising `ValidationError` with the right `loc`.

**Done when:** the t1 unit tests pass and `devbox run quality` is green. The acceptance tests need t2.

## t2 — Expose POST /tasks and GET /tasks and wire the store into the app

**Files:** src/taskboard19_api/tasks/router.py, src/taskboard19_api/tasks/__init__.py, src/taskboard19_api/main.py
**Covers:** AC-001.1, AC-001.2, AC-001.3, AC-001.4, AC-001.5, AC-001.6, AC-001.7
**Goal:** Serve the contract in design.md: `POST /tasks` (201, or 422 in FastAPI's standard shape) and `GET /tasks` (200 with an array in creation order), backed by a store that a restart empties.

**Implementation notes:**
- `router.py`: `APIRouter(tags=["tasks"])`. `get_task_store(request) -> TaskStore` returns `request.app.state.task_store`.
- `POST /tasks`: `status_code=201`, `response_model=Task`, body `TaskCreate`, sync `def`. Emit structlog event `task_created` with `task_id` (never the title, to keep user content out of logs).
- `GET /tasks`: `response_model=list[Task]`, returns `store.list()`.
- `main.py`: set `app.state.task_store = TaskStore()` right after creating `app`. Add a `lifespan` context manager (passed to `FastAPI(...)`) that assigns a fresh `TaskStore()` at startup. Then `app.include_router(tasks.router)`.
- Keep `/health`, `/ready`, `/ping`, `/metrics` and the middleware unchanged.
- Add the `router` export to `tasks/__init__.py`.

**Done when:** the acceptance tests for AC-001.1 to AC-001.7 pass, the existing tests in `tests/` still pass, and `devbox run ci` is green.
