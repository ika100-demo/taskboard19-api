"""Request and response models for tasks (spec 001)."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, StrictStr, field_validator

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TaskCreate(BaseModel):
    title: StrictStr = Field(min_length=1, max_length=200)
    due_date: date | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must contain a non-whitespace character")
        return value

    @field_validator("due_date", mode="before")
    @classmethod
    def _due_date_format(cls, value: Any) -> Any:
        if value is None:
            return None
        if not isinstance(value, str) or not _DATE_RE.match(value):
            raise ValueError("due_date must be a YYYY-MM-DD date")
        return date.fromisoformat(value)


class Task(BaseModel):
    id: int = Field(ge=1)
    title: str
    due_date: date | None
    created_at: datetime
