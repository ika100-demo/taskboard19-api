---
spec_id: 001-create-and-list-tasks-in-memory
title: Create and list tasks in memory
status: done
priority: P1
shape: service-python
---

# 001 — Create and list tasks in memory

## Problem

The Task API has no tasks yet: it answers health, readiness and ping, but a client cannot record anything to do or read it back. This first feature lets a client create a task with a title and an optional due date and list all tasks, so that clients can be built against a real task resource. Tasks live only in the running service's memory; durable storage comes later.

## Stories

As an API client, I want to create a task with a title and, if I know it, a due date, so that I can record what needs doing.

As an API client, I want to list all tasks, so that I can show what is recorded.

## Acceptance criteria

- **AC-001.1** Given the service is running, when a client sends `POST /tasks` with JSON `{"title": "Buy milk", "due_date": "2026-12-01"}`, then the response is 201 with a JSON body holding `id` (a positive integer), `title` "Buy milk", `due_date` "2026-12-01" and `created_at` (an ISO 8601 UTC timestamp). (smoke)
- **AC-001.2** Given the service is running, when a client sends `POST /tasks` with only `{"title": "Call Bob"}` or with `"due_date": null`, then the response is 201 and the returned task has `due_date` null.
- **AC-001.3** Given the service is running, when a client sends `POST /tasks` whose `title` is missing, not a string, empty, only whitespace or longer than 200 characters, then the response is 422 with an error body naming the field `title`, and no task is added to the list.
- **AC-001.4** Given the service is running, when a client sends `POST /tasks` whose `due_date` is not a calendar date in `YYYY-MM-DD` form (for example "tomorrow", "2026-13-01" or "2026-12-01T10:00:00"), then the response is 422 with an error body naming the field `due_date`, and no task is added to the list.
- **AC-001.5** Given tasks "A", "B" and "C" were created in that order, when a client sends `GET /tasks`, then the response is 200 with a JSON array of those three tasks in creation order, each with the same `id`, `title`, `due_date` and `created_at` returned when it was created. (smoke)
- **AC-001.6** Given no task has been created since the service started, when a client sends `GET /tasks`, then the response is 200 with an empty JSON array.
- **AC-001.7** Given two tasks were created, when the service restarts and a client sends `GET /tasks`, then the response is 200 with an empty JSON array, and the next task created gets `id` 1.

## Non-goals

- Durable storage; tasks surviving a restart or being shared between replicas.
- Reading, updating, completing or deleting a single task.
- Filtering, sorting options and pagination of the list.
- Fields beyond title and due date (description, status, assignee, priority).
- Authentication and per-user task lists: anyone who can reach the service may create and list tasks; authentication comes in a later spec.

## Assumptions

- **A1** The resource lives at `/tasks`, and the fields are `id`, `title`, `due_date`, `created_at` (other option: other paths or names, e.g. `/api/v1/tasks`, `dueDate`; affects AC-001.1, AC-001.2, AC-001.5).
- **A2** `id` is an integer assigned by the service, starting at 1 and increasing by 1 per created task (other option: a UUID string; affects AC-001.1, AC-001.7).
- **A3** The due date is a calendar date without time (`YYYY-MM-DD`), and dates in the past are accepted (other option: a full timestamp, or rejecting past dates; affects AC-001.1, AC-001.4).
- **A4** A title is 1 to 200 characters, must contain a non-whitespace character and is stored exactly as sent; duplicate titles are allowed (other option: trim whitespace, a different limit, unique titles; affects AC-001.3).
- **A5** Validation errors answer 422 in the framework's standard error shape, which names the failing field (other option: 400 with a custom error body; affects AC-001.3, AC-001.4).
- **A6** The list returns every task in creation order with no upper limit, because memory is the only store and pagination is a non-goal (other option: a cap such as 1000 tasks with a 507/409 when full; affects AC-001.5).
- **A7** Each running instance keeps its own tasks; a restart empties the list and restarts the id counter (other option: none without durable storage; affects AC-001.7).

## Open questions

- ~~May anyone who can reach the service create and list tasks without authentication? (suggested: yes, for now; authentication is a later spec; affects AC-001.1, AC-001.5)~~ Answered 2026-11-15: yes, for now; authentication is a later spec. Folded into the non-goals.

## Changelog

- 2026-11-15 created
- 2026-11-15 amended: open question on authentication answered (no authentication for now), folded into the non-goals; no criteria changed
- 2026-11-15 approved
- 2026-11-15 building
- 2026-11-15 done
