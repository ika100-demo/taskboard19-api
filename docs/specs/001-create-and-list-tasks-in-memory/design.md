# Design — 001 Create and list tasks in memory

## Decisions

- Tasks live in a `TaskStore` held on `app.state.task_store`, handed to routes through a FastAPI dependency (`get_task_store`). A later durable store replaces the class behind the same three methods without touching the routes. Feature-local, so no ADR.
- The store is created once at import, so a plain `TestClient(app)` works. The app lifespan swaps in a fresh store at every startup, so a process restart, or entering `with TestClient(app)` again in tests, empties the list and resets ids to 1 (AC-001.7, A7).
- The store guards its counter and list with a `threading.Lock`, because sync FastAPI routes run in a thread pool. The image runs one uvicorn worker (Dockerfile `CMD`), so one process holds one list. Replicas each keep their own list (non-goal).
- Validation errors use FastAPI's standard 422 body (A5), with no custom exception handler.
- `due_date` is checked strictly before pydantic parses it: it must be a JSON string matching `^\d{4}-\d{2}-\d{2}$` and a valid calendar date. Pydantic's lax `date` would accept unix-timestamp integers and `...T00:00:00` datetimes, and both must be rejected (AC-001.4).
- `title` is a strict string (no coercion), 1–200 characters, with at least one non-whitespace character. It is stored exactly as sent, with no stripping (A4, AC-001.3).
- Unknown extra fields in the request body are ignored (pydantic default). The spec does not ask for rejecting them.

## Modules

| Module | Responsibility | New / changed |
|---|---|---|
| `src/taskboard19_api/tasks/__init__.py` | package marker; exports `router`, `TaskStore` | new |
| `src/taskboard19_api/tasks/models.py` | `TaskCreate` (request, validation), `Task` (response/stored record) | new |
| `src/taskboard19_api/tasks/store.py` | `TaskStore`: in-memory, thread-safe, sequential ids | new |
| `src/taskboard19_api/tasks/router.py` | `APIRouter` with `POST /tasks`, `GET /tasks`; `get_task_store` dependency; structured log on create | new |
| `src/taskboard19_api/main.py` | include router; lifespan that resets `app.state.task_store` | changed |

Interfaces (signatures, not code):

```python
class TaskCreate(BaseModel):
    title: StrictStr          # 1..200 chars, must contain a non-whitespace char
    due_date: date | None = None   # before-validator: None or str matching ^\d{4}-\d{2}-\d{2}$ and valid date

class Task(BaseModel):
    id: int                   # >= 1
    title: str
    due_date: date | None
    created_at: datetime      # timezone-aware UTC

class TaskStore:
    def create(self, title: str, due_date: date | None) -> Task: ...  # id = previous + 1, created_at = now(UTC)
    def list(self) -> list[Task]: ...                                  # copy, creation order
    def clear(self) -> None: ...                                       # empties list, next id = 1

def get_task_store(request: Request) -> TaskStore: ...  # returns request.app.state.task_store
```

## Contract

All bodies are `application/json`. No authentication (non-goal).

### `POST /tasks`

Request body:

| Field | Type | Required | Rule |
|---|---|---|---|
| `title` | string | yes | 1–200 characters, at least one non-whitespace character, stored as sent |
| `due_date` | string \| null | no (default null) | `YYYY-MM-DD`, a real calendar date; past dates allowed |

Responses:

- `201 Created`: the created task (AC-001.1, AC-001.2):
  ```json
  {"id": 1, "title": "Buy milk", "due_date": "2026-12-01", "created_at": "2026-11-15T09:30:12.345678Z"}
  ```
  - `id`: integer, 1 for the first task since start, +1 per created task (A2, AC-001.7).
  - `due_date`: the `YYYY-MM-DD` string, or `null` when omitted or sent as `null`.
  - `created_at`: ISO 8601 / RFC 3339 UTC timestamp with the `Z` suffix (pydantic v2 serialization of an aware UTC datetime). Fractional seconds may be present.
- `422 Unprocessable Entity`: FastAPI's standard validation body. No task is stored (AC-001.3, AC-001.4):
  ```json
  {"detail": [{"type": "string_too_short", "loc": ["body", "title"], "msg": "...", "input": ""}]}
  ```
  - A bad `title` (missing, non-string, empty, whitespace only, >200 chars) has at least one `detail` entry with `loc == ["body", "title"]`.
  - A bad `due_date` (non-string, wrong form such as `"tomorrow"`, `"2026-12-01T10:00:00"`, or an impossible date such as `"2026-13-01"`) has at least one `detail` entry with `loc == ["body", "due_date"]`.
  - `type` and `msg` values are not part of the contract. Tests assert on `loc` only.
  - A body that is not a JSON object also answers 422, with `loc` starting `["body"]`.

### `GET /tasks`

- `200 OK`: a JSON array of every task in creation order, with each element exactly as returned by its `POST` (AC-001.5). It is `[]` when no task was created since start (AC-001.6). There are no query parameters, no pagination and no limit (A6).

### Test seams

- `taskboard19_api.main.app.state.task_store` is the live `TaskStore`.
- A restart is simulated by entering a new `with TestClient(app):` block. The lifespan startup replaces the store, so the list is empty and the next id is 1 (AC-001.7). Fixtures that need isolation between tests use the context-manager form, or call `app.state.task_store.clear()`.
- Smoke: `GET /tasks` is read-only and safe in every environment. `POST /tasks` smoke tests must carry `@pytest.mark.writes` and use a `smoke-<uuid>` title.

## Data

In memory only: a `list[Task]` plus a next-id counter inside `TaskStore`. No migration, no new dependency, no new env var.
