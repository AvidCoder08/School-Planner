from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CourseResult:
    credits: int
    grade_point: int


def calc_sgpa(courses: Iterable[CourseResult]) -> float:
    weighted = 0.0
    total_credits = 0
    for c in courses:
        weighted += c.credits * c.grade_point
        total_credits += c.credits
    if total_credits == 0:
        return 0.0
    return round(weighted / total_credits, 2)


def calc_cgpa(semester_courses: Iterable[Iterable[CourseResult]]) -> float:
    weighted = 0.0
    total_credits = 0
    for sem in semester_courses:
        for c in sem:
            weighted += c.credits * c.grade_point
            total_credits += c.credits
    if total_credits == 0:
        return 0.0
    return round(weighted / total_credits, 2)
