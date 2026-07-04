from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class AssessmentRule:
    max_raw: float
    reduced_to: float


RULES_BY_CREDITS: Dict[int, Dict[str, AssessmentRule]] = {
    2: {
        "ISA1": AssessmentRule(30, 25),
        "ISA2": AssessmentRule(30, 25),
        "ESA": AssessmentRule(50, 50),
    },
    4: {
        "ISA1": AssessmentRule(40, 20),
        "ISA2": AssessmentRule(40, 20),
        "ESA": AssessmentRule(100, 50),
        "A1": AssessmentRule(10, 2.5),
        "A2": AssessmentRule(10, 2.5),
        "A3": AssessmentRule(10, 2.5),
        "A4": AssessmentRule(10, 2.5),
    },
    5: {
        "ISA1": AssessmentRule(40, 20),
        "ISA2": AssessmentRule(40, 20),
        "ESA": AssessmentRule(100, 50),
        "A1": AssessmentRule(10, 2.5),
        "A2": AssessmentRule(10, 2.5),
        "A3": AssessmentRule(10, 2.5),
        "A4": AssessmentRule(10, 2.5),
        "LAB": AssessmentRule(20, 20),
    },
}


def _scale_to_weighted(raw_score: float, max_raw: float, reduced_to: float) -> float:
    if max_raw <= 0:
        raise ValueError("max_raw must be greater than 0")
    clamped = max(0.0, min(raw_score, max_raw))
    return (clamped / max_raw) * reduced_to


def calculate_subject_score(
    credits: int,
    raw_scores: Dict[str, float],
    *,
    round_to: int = 2,
) -> float:
    if credits not in RULES_BY_CREDITS:
        raise ValueError(f"Unsupported credit model: {credits}. Use 2, 4, or 5.")

    rules = RULES_BY_CREDITS[credits]

    missing = [name for name in rules if name not in raw_scores]
    if missing:
        raise ValueError(f"Missing required assessment scores: {', '.join(missing)}")

    total = 0.0
    for name, rule in rules.items():
        total += _scale_to_weighted(raw_scores[name], rule.max_raw, rule.reduced_to)

    return round(total, round_to)


def to_letter_grade(score_100: float) -> str:
    score = max(0.0, min(score_100, 100.0))
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    if score >= 50:
        return "D"
    if score >= 40:
        return "E"
    return "F"


def to_grade_point(letter_grade: str) -> int:
    mapping = {
        "S": 10,
        "A": 9,
        "B": 8,
        "C": 7,
        "D": 6,
        "E": 5,
        "F": 4,
    }
    try:
        return mapping[letter_grade.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported letter grade: {letter_grade}") from exc


def evaluate_subject(credits: int, raw_scores: Dict[str, float]) -> Tuple[float, str, int]:
    score = calculate_subject_score(credits, raw_scores)
    letter = to_letter_grade(score)
    point = to_grade_point(letter)
    return score, letter, point
