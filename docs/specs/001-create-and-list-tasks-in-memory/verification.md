# Verification — 001 Create and list tasks in memory

**Result:** pass
**Commit:** ea56e84 · **Base:** c0ad80e · **Trace:** 7/7 criteria named by tests (smoke: AC-001.1, AC-001.5)

| Criterion | Verdict | Tests | Implementation | Notes |
|---|---|---|---|---|
| AC-001.1 | met | `tests/test_tasks.py::test_create_task_with_title_and_due_date`, `tests/test_smoke_tasks.py::test_smoke_create_task` | `src/taskboard19_api/tasks/router.py:25`, `src/taskboard19_api/tasks/store.py:17` | asserts 201, `id` a positive int (not bool), exact `title`/`due_date`, `created_at` ends in `Z`, parses with UTC offset 0 |
| AC-001.2 | met | `tests/test_tasks.py::test_create_task_without_due_date`, `::test_create_task_with_null_due_date` | `src/taskboard19_api/tasks/models.py:16`, `src/taskboard19_api/tasks/models.py:28` | both forms (omitted, `null`) assert 201 and `due_date is None` |
| AC-001.3 | met | `tests/test_tasks.py::test_invalid_title_rejected` (8 cases), `::test_title_200_chars_accepted`, `tests/test_smoke_tasks.py::test_smoke_create_task_rejects_empty_title` | `src/taskboard19_api/tasks/models.py:15`, `src/taskboard19_api/tasks/models.py:18` | missing, int/null/list, empty, whitespace, 201 chars: 422, `["body","title"]` in `loc`, list stays `[]`; 200-char boundary accepted |
| AC-001.4 | met | `tests/test_tasks.py::test_invalid_due_date_rejected` (5 cases) | `src/taskboard19_api/tasks/models.py:25` | all three spec examples plus integer and empty: 422, `["body","due_date"]` in `loc`, list stays `[]`; strict regex + `date.fromisoformat` |
| AC-001.5 | met | `tests/test_tasks.py::test_list_returns_tasks_in_creation_order`, `tests/test_smoke_tasks.py::test_smoke_list_tasks_in_creation_order` | `src/taskboard19_api/tasks/router.py:34`, `src/taskboard19_api/tasks/store.py:29` | creates A, B, C; asserts 200 and `body == created` (same order and all four fields) |
| AC-001.6 | met | `tests/test_tasks.py::test_list_is_empty_initially` | `src/taskboard19_api/main.py:29`, `src/taskboard19_api/tasks/store.py:14` | fresh lifespan start, asserts 200 and `[]` |
| AC-001.7 | met | `tests/test_tasks.py::test_restart_empties_list_and_resets_ids` | `src/taskboard19_api/main.py:27`, `src/taskboard19_api/main.py:33` | two tasks, new `with TestClient(app)` (lifespan restart): list `[]`, next `id == 1` |

## Non-goals

No durable storage, no single-task read/update/delete routes, no filtering, sorting or pagination, no extra fields, no authentication. `main.py` keeps `/health`, `/ready`, `/ping`, `/metrics` and the middleware unchanged; only the lifespan, store and router were added. ✔

## Deviations from the plan

- `tests/test_tasks.py` and `tests/test_smoke_tasks.py` are in no task's `files`: these are the acceptance tests written red-first before the plan's tasks (commits 5281e45, 1d6612a); acceptable.
- `docs/specs/001-.../{spec,plan,design}.md` changed: spec status `building` plus Changelog line, plan and design added by the pipeline; acceptable.
- Both tasks t1 and t2 have `done: true`; files match the tasks otherwise.

## Contract

Matches `design.md`: `POST /tasks` 201 with `Task` / FastAPI standard 422, `GET /tasks` 200 array in creation order, `TaskStore` with `create`/`list`/`clear` under one `threading.Lock`, `get_task_store` dependency on `app.state.task_store`, lifespan resets the store, `task_created` log with `task_id` only. ✔

## Smoke tests

`tests/test_smoke_tasks.py`: the two writing tests carry `@pytest.mark.writes` and use `smoke-<uuid>` titles; the read-only list and empty-title checks keep staging and prod covered. Each fails without the `/tasks` routes (404). No smoke findings.

## Mutation check (report only)

17 of 19 mutants of the changed code were caught by the acceptance tests (89 %; spec 152, report only).

Survived (a test that names the criterion would fail if it checked this):
- `src/taskboard19_api/tasks/store.py:26 1 → 2`
- `src/taskboard19_api/tasks/store.py:36 1 → 2`
