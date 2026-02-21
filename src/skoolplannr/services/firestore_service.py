from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    from google.cloud import firestore
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Missing dependency 'google-cloud-firestore'. Run run.bat or install requirements.txt."
    ) from exc

from skoolplannr.config.settings import settings
from skoolplannr.core.grades import RULES_BY_CREDITS, evaluate_subject
from skoolplannr.core.gpa import calculate_cgpa, calculate_sgpa


class FirestoreServiceError(Exception):
    pass


class FirestoreService:
    def __init__(self, project_id: str) -> None:
        if not project_id:
            raise FirestoreServiceError("Missing FIREBASE_PROJECT_ID in environment")
        self.db = firestore.Client(project=project_id)

    @classmethod
    def from_settings(cls) -> "FirestoreService":
        return cls(settings.firebase_project_id)

    def ensure_user_profile(self, uid: str, email: str) -> None:
        ref = self.db.collection("users").document(uid)
        if not ref.get().exists:
            ref.set(
                {
                    "email": email,
                    "created_at": datetime.now(timezone.utc),
                    "active_year_id": None,
                    "active_term_id": None,
                }
            )

    def get_profile(self, uid: str) -> Dict:
        snap = self.db.collection("users").document(uid).get()
        if not snap.exists:
            return {}
        return snap.to_dict() or {}

    def has_onboarding(self, uid: str) -> bool:
        years = (
            self.db.collection("users")
            .document(uid)
            .collection("academic_years")
            .limit(1)
            .stream()
        )
        return any(True for _ in years)

    def save_onboarding(
        self,
        uid: str,
        year_label: str,
        year_start: datetime,
        year_end: datetime,
        terms: List[Dict[str, datetime]],
    ) -> None:
        if not terms:
            raise FirestoreServiceError("At least one term is required.")

        user_ref = self.db.collection("users").document(uid)
        year_ref = user_ref.collection("academic_years").document()

        year_ref.set(
            {
                "label": year_label,
                "start_date": year_start,
                "end_date": year_end,
            }
        )

        active_term_id = None
        for index, term in enumerate(terms):
            term_ref = year_ref.collection("terms").document()
            term_ref.set(
                {
                    "name": term["name"],
                    "start_date": term["start_date"],
                    "end_date": term["end_date"],
                    "status": "active" if index == 0 else "upcoming",
                    "sgpa": None,
                }
            )
            if index == 0:
                active_term_id = term_ref.id

        user_ref.update(
            {
                "active_year_id": year_ref.id,
                "active_term_id": active_term_id,
            }
        )

    def _active_term_ref(self, uid: str):
        profile = self.get_profile(uid)
        year_id = profile.get("active_year_id")
        term_id = profile.get("active_term_id")
        if not year_id or not term_id:
            raise FirestoreServiceError("Active academic year/term not set. Complete onboarding first.")

        return (
            self.db.collection("users")
            .document(uid)
            .collection("academic_years")
            .document(year_id)
            .collection("terms")
            .document(term_id)
        )

    def list_years_and_terms(self, uid: str) -> List[Dict]:
        user_ref = self.db.collection("users").document(uid)
        years_snap = user_ref.collection("academic_years").stream()
        results = []
        
        for year_doc in years_snap:
            year_data = year_doc.to_dict() or {}
            year_id = year_doc.id
            year_label = year_data.get("label", year_id)
            
            terms_snap = user_ref.collection("academic_years").document(year_id).collection("terms").stream()
            term_list = []
            for term_doc in terms_snap:
                term_data = term_doc.to_dict() or {}
                term_list.append({
                    "id": term_doc.id,
                    "name": term_data.get("name", term_doc.id),
                    "start_date": term_data.get("start_date")
                })
            
            term_list.sort(key=lambda t: t.get("start_date") or datetime.min.replace(tzinfo=timezone.utc))
            
            results.append({
                "id": year_id,
                "label": year_label,
                "start_date": year_data.get("start_date"),
                "terms": term_list
            })
            
        results.sort(key=lambda y: y.get("start_date") or datetime.min.replace(tzinfo=timezone.utc))
        return results

    def set_active_term(self, uid: str, year_id: str, term_id: str) -> None:
        user_ref = self.db.collection("users").document(uid)
        user_ref.update({
            "active_year_id": year_id,
            "active_term_id": term_id,
        })

    def list_subjects(self, uid: str) -> List[Dict]:
        term_ref = self._active_term_ref(uid)
        docs = term_ref.collection("subjects").stream()
        results: List[Dict] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        return results

    def create_subject(
        self,
        uid: str,
        *,
        name: str,
        instructor: str,
        location: str,
        credits: int,
        schedule_slots: List[Dict[str, str]],
    ) -> str:
        term_ref = self._active_term_ref(uid)
        ref = term_ref.collection("subjects").document()
        ref.set(
            {
                "name": name,
                "instructor": instructor,
                "location": location,
                "credits": credits,
                "schedule_slots": schedule_slots,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return ref.id

    def delete_subject(self, uid: str, subject_id: str) -> None:
        term_ref = self._active_term_ref(uid)
        term_ref.collection("subjects").document(subject_id).delete()

    def list_tasks(self, uid: str, include_completed: bool = True) -> List[Dict]:
        term_ref = self._active_term_ref(uid)
        docs = term_ref.collection("tasks").stream()
        results: List[Dict] = []
        for doc in docs:
            data = doc.to_dict() or {}
            if not include_completed and data.get("completed"):
                continue
            data["id"] = doc.id
            results.append(data)
        results.sort(key=lambda row: row.get("due_at") or datetime.max.replace(tzinfo=timezone.utc))
        return results

    def create_task(
        self,
        uid: str,
        *,
        title: str,
        description: str,
        subject_id: Optional[str],
        task_type: str,
        due_at: datetime,
        priority: str,
    ) -> str:
        term_ref = self._active_term_ref(uid)
        ref = term_ref.collection("tasks").document()
        ref.set(
            {
                "title": title,
                "description": description,
                "subject_id": subject_id,
                "task_type": task_type,
                "due_at": due_at,
                "completed": False,
                "priority": priority,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return ref.id

    def set_task_completed(self, uid: str, task_id: str, completed: bool) -> None:
        term_ref = self._active_term_ref(uid)
        term_ref.collection("tasks").document(task_id).update({"completed": completed})

    def delete_task(self, uid: str, task_id: str) -> None:
        term_ref = self._active_term_ref(uid)
        term_ref.collection("tasks").document(task_id).delete()

    def list_events(self, uid: str) -> List[Dict]:
        term_ref = self._active_term_ref(uid)
        docs = term_ref.collection("events").stream()
        results: List[Dict] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        results.sort(key=lambda row: row.get("starts_at") or datetime.max.replace(tzinfo=timezone.utc))
        return results

    def create_event(
        self,
        uid: str,
        *,
        title: str,
        event_type: str,
        starts_at: datetime,
        ends_at: datetime,
        subject_id: Optional[str],
    ) -> str:
        term_ref = self._active_term_ref(uid)
        ref = term_ref.collection("events").document()
        ref.set(
            {
                "title": title,
                "event_type": event_type,
                "starts_at": starts_at,
                "ends_at": ends_at,
                "subject_id": subject_id,
                "created_at": datetime.now(timezone.utc),
            }
        )
        return ref.id

    def delete_event(self, uid: str, event_id: str) -> None:
        term_ref = self._active_term_ref(uid)
        term_ref.collection("events").document(event_id).delete()

    def get_subject(self, uid: str, subject_id: str) -> Dict:
        term_ref = self._active_term_ref(uid)
        snap = term_ref.collection("subjects").document(subject_id).get()
        if not snap.exists:
            return {}
        data = snap.to_dict() or {}
        data["id"] = snap.id
        return data

    def get_assessments(self, uid: str, subject_id: str) -> Dict[str, float]:
        term_ref = self._active_term_ref(uid)
        docs = term_ref.collection("subjects").document(subject_id).collection("assessments").stream()
        results: Dict[str, float] = {}
        for doc in docs:
            data = doc.to_dict() or {}
            if "type" in data and "score_raw" in data:
                results[str(data["type"])] = float(data["score_raw"])
        return results

    def save_assessments_and_grade(self, uid: str, subject_id: str, raw_scores: Dict[str, float]) -> Dict:
        subject = self.get_subject(uid, subject_id)
        if not subject:
            raise FirestoreServiceError("Subject not found for grade input.")

        credits = int(subject.get("credits", 0))
        if credits not in RULES_BY_CREDITS:
            raise FirestoreServiceError("Unsupported credit model for subject.")

        rules = RULES_BY_CREDITS[credits]
        
        term_ref = self._active_term_ref(uid)
        assess_ref = term_ref.collection("subjects").document(subject_id).collection("assessments")

        for name, rule in rules.items():
            if name in raw_scores:
                raw = float(raw_scores[name])
                weighted = (max(0.0, min(raw, rule.max_raw)) / rule.max_raw) * rule.reduced_to
                assess_ref.document(name).set(
                    {
                        "type": name,
                        "max_raw": rule.max_raw,
                        "weight_to": rule.reduced_to,
                        "score_raw": raw,
                        "score_weighted": round(weighted, 2),
                    }
                )
            else:
                assess_ref.document(name).delete()

        missing = [name for name in rules if name not in raw_scores]
        if missing:
            term_ref.collection("grades").document(subject_id).delete()
            return {
                "partial": True,
                "missing": missing,
                "subject_id": subject_id,
            }

        final_score, letter_grade, grade_point = evaluate_subject(credits, raw_scores)

        grade_doc = {
            "partial": False,
            "subject_id": subject_id,
            "subject_name": subject.get("name", ""),
            "credits": credits,
            "final_score_100": final_score,
            "letter_grade": letter_grade,
            "grade_point": grade_point,
            "updated_at": datetime.now(timezone.utc),
        }

        term_ref.collection("grades").document(subject_id).set(grade_doc)
        return grade_doc

    def list_grades(self, uid: str) -> List[Dict]:
        term_ref = self._active_term_ref(uid)
        docs = term_ref.collection("grades").stream()
        results: List[Dict] = []
        for doc in docs:
            data = doc.to_dict() or {}
            data["id"] = doc.id
            results.append(data)
        results.sort(key=lambda row: row.get("subject_name", ""))
        return results

    def calculate_and_store_sgpa(self, uid: str) -> Tuple[float, int]:
        grades = self.list_grades(uid)
        if not grades:
            raise FirestoreServiceError("No grades found to calculate SGPA.")

        course_results = []
        total_credits = 0
        for grade in grades:
            credits = int(grade.get("credits", 0))
            grade_point = int(grade.get("grade_point", 0))
            if credits <= 0:
                continue
            course_results.append((credits, grade_point))
            total_credits += credits

        sgpa = calculate_sgpa(course_results)

        term_ref = self._active_term_ref(uid)
        term_ref.set({"sgpa": sgpa, "total_credits": total_credits}, merge=True)
        return sgpa, total_credits

    def calculate_and_store_cgpa(self, uid: str) -> Tuple[float, List[Dict]]:
        user_ref = self.db.collection("users").document(uid)
        years = user_ref.collection("academic_years").stream()

        semester_results = []
        trend: List[Dict] = []
        for year_doc in years:
            year = year_doc.to_dict() or {}
            year_label = year.get("label", year_doc.id)
            terms = year_doc.reference.collection("terms").stream()
            for term_doc in terms:
                term = term_doc.to_dict() or {}
                sgpa = term.get("sgpa")
                credits = term.get("total_credits")
                if sgpa is None or not credits:
                    continue
                semester_results.append((float(sgpa), int(credits)))
                trend.append(
                    {
                        "label": f"{year_label} - {term.get('name', term_doc.id)}",
                        "sgpa": float(sgpa),
                        "credits": int(credits),
                    }
                )

        if not semester_results:
            raise FirestoreServiceError("No semester results found for CGPA.")

        cgpa = calculate_cgpa(semester_results)
        user_ref.set({"cgpa": cgpa}, merge=True)
        return cgpa, trend

    def get_cached_cgpa(self, uid: str) -> Optional[float]:
        profile = self.get_profile(uid)
        value = profile.get("cgpa")
        if value is None:
            return None
        return float(value)

    def get_active_term_summary(self, uid: str) -> Dict:
        term_ref = self._active_term_ref(uid)
        snap = term_ref.get()
        if not snap.exists:
            return {}
        return snap.to_dict() or {}
