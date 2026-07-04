import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from skoolplannr.services.appwrite_service import AppwriteService


class AppwriteGradeOverviewTests(unittest.TestCase):
    def test_get_grades_overview_returns_grades_and_summary(self):
        service = AppwriteService.__new__(AppwriteService)
        service.list_grades = MagicMock(
            return_value=[
                {
                    "subject_id": "sub-1",
                    "subject_name": "Discrete Math",
                    "grade_point": 9,
                }
            ]
        )
        service.get_cached_cgpa = MagicMock(return_value=8.42)
        service.get_active_term_summary = MagicMock(
            return_value={"name": "Semester 1", "sgpa": 8.75, "total_credits": 20}
        )

        overview = AppwriteService.get_grades_overview(service, "user-1")

        self.assertEqual(len(overview["grades"]), 1)
        self.assertEqual(overview["grades"][0]["subject_name"], "Discrete Math")
        self.assertEqual(overview["summary"]["sgpa"], 8.75)
        self.assertEqual(overview["summary"]["cgpa"], 8.42)
        self.assertEqual(overview["summary"]["total_credits"], 20)
        self.assertEqual(overview["summary"]["active_term_name"], "Semester 1")

    def test_save_assessments_and_grade_recomputes_sgpa_and_cgpa(self):
        service = AppwriteService.__new__(AppwriteService)
        service.assessments_collection_id = "assessments"
        service.grades_collection_id = "grades"
        service.get_subject = MagicMock(return_value={"name": "Discrete Math", "credits": 4})
        service._list_documents = MagicMock(return_value=[])
        service._find_first = MagicMock(return_value=None)
        service._create_document = MagicMock(return_value={"$id": "grade-doc"})
        service._update_document = MagicMock(return_value={"$id": "grade-doc"})
        service._delete_document = MagicMock()
        service.calculate_and_store_sgpa = MagicMock(return_value=(8.5, 4))
        service.calculate_and_store_cgpa = MagicMock(return_value=(8.75, []))

        raw_scores = {"ISA1": 32, "ISA2": 34, "ESA": 92, "A1": 9, "A2": 9, "A3": 10, "A4": 10}
        result = AppwriteService.save_assessments_and_grade(service, "user-1", "sub-1", raw_scores)

        self.assertFalse(result["partial"])
        self.assertEqual(result["sgpa"], 8.5)
        self.assertEqual(result["cgpa"], 8.75)
        self.assertEqual(result["total_credits"], 4)
        service.calculate_and_store_sgpa.assert_called_once_with("user-1")
        service.calculate_and_store_cgpa.assert_called_once_with("user-1")


if __name__ == "__main__":
    unittest.main()