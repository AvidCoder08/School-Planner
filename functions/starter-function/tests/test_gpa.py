import unittest

from app.domain.logic.gpa import CourseResult, calc_cgpa, calc_sgpa


class GPATests(unittest.TestCase):
    def test_sgpa(self):
        courses = [CourseResult(4, 9), CourseResult(5, 8), CourseResult(2, 10)]
        self.assertAlmostEqual(calc_sgpa(courses), 8.73, places=2)

    def test_cgpa(self):
        sem1 = [CourseResult(4, 8), CourseResult(4, 9)]
        sem2 = [CourseResult(5, 10), CourseResult(2, 8)]
        self.assertAlmostEqual(calc_cgpa([sem1, sem2]), 8.93, places=2)


if __name__ == "__main__":
    unittest.main()
