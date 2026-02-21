from typing import Iterable, Tuple


def calculate_sgpa(course_results: Iterable[Tuple[int, int]], *, round_to: int = 2) -> float:
    """
    course_results: iterable of (credits, grade_point)
    SGPA = Σ(credits * grade_point) / Σ(credits)
    """
    weighted_sum = 0.0
    total_credits = 0

    for credits, grade_point in course_results:
        if credits <= 0:
            raise ValueError("Course credits must be greater than 0")
        weighted_sum += credits * grade_point
        total_credits += credits

    if total_credits == 0:
        raise ValueError("Cannot calculate SGPA with zero total credits")

    return round(weighted_sum / total_credits, round_to)


def calculate_cgpa(semester_results: Iterable[Tuple[float, int]], *, round_to: int = 2) -> float:
    """
    semester_results: iterable of (sgpa, semester_total_credits)
    CGPA = Σ(sgpa * semester_credits) / Σ(semester_credits)
    """
    weighted_sum = 0.0
    total_credits = 0

    for sgpa, credits in semester_results:
        if credits <= 0:
            raise ValueError("Semester credits must be greater than 0")
        weighted_sum += sgpa * credits
        total_credits += credits

    if total_credits == 0:
        raise ValueError("Cannot calculate CGPA with zero total credits")

    return round(weighted_sum / total_credits, round_to)
