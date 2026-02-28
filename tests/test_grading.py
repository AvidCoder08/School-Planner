import unittest

from app.domain.logic.grading import calc_subject_final, grade_from_marks


class GradingTests(unittest.TestCase):
    def test_grade_bands(self):
        self.assertEqual(grade_from_marks(95)[0], "S")
        self.assertEqual(grade_from_marks(84)[0], "A")
        self.assertEqual(grade_from_marks(20)[0], "F")

    def test_4_credit_calculation(self):
        marks = calc_subject_final(4, [(40, 50), (42, 50), (88, 100), (16, 20)])
        self.assertAlmostEqual(marks, 84.55, places=2)

    def test_5_credit_calculation(self):
        marks = calc_subject_final(5, [(40, 50), (41, 50), (90, 100), (18, 20)], lab_marks=18, lab_max=20)
        self.assertGreater(marks, 80)


if __name__ == "__main__":
    unittest.main()
