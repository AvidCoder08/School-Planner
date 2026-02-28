from __future__ import annotations

from typing import Iterable

GRADE_BANDS: list[tuple[int, int, str, int]] = [
    (90, 100, "S", 10),
    (80, 89, "A", 9),
    (70, 79, "B", 8),
    (60, 69, "C", 7),
    (50, 59, "D", 6),
    (40, 49, "E", 5),
    (0, 39, "F", 4),
]


def clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def grade_from_marks(marks: float) -> tuple[str, int]:
    rounded = int(round(clamp_0_100(marks)))
    for low, high, letter, points in GRADE_BANDS:
        if low <= rounded <= high:
            return letter, points
    return "F", 4


def calc_weighted_total(components: Iterable[tuple[float, float]]) -> float:
    obtained = 0.0
    maximum = 0.0
    for score, max_marks in components:
        obtained += score
        maximum += max_marks
    if maximum <= 0:
        return 0.0
    return clamp_0_100((obtained / maximum) * 100)


def calc_subject_final(
    credits: int,
    theory_components: Iterable[tuple[float, float]],
    lab_marks: float | None = None,
    lab_max: float = 20,
) -> float:
    theory_pct = calc_weighted_total(theory_components)
    if credits in (2, 4):
        return theory_pct
    if credits == 5:
        if lab_marks is None or lab_max <= 0:
            raise ValueError("5-credit subjects require lab_marks and positive lab_max")
        lab_pct = clamp_0_100((lab_marks / lab_max) * 100)
        return clamp_0_100(theory_pct * 0.80 + lab_pct * 0.20)
    raise ValueError("Unsupported credits; expected 2, 4, or 5")
