from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    academic_year: str | None
    semester_name: str | None
    semester_start: str | None
    semester_end: str | None


@dataclass
class Subject:
    id: int
    user_id: int
    name: str
    location: str
    instructor: str
    credits: int
    day_of_week: str
    start_time: str
    end_time: str


@dataclass
class Task:
    id: int
    user_id: int
    title: str
    task_type: str
    subject_id: int | None
    due_at: str
    is_completed: bool


@dataclass
class GradeRecord:
    id: int
    user_id: int
    subject_id: int
    isa1: float
    isa2: float
    esa: float
    assignments: float
    lab_marks: float | None
    updated_at: datetime
