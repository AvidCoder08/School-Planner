from datetime import datetime, timezone
import json
from typing import Dict, List, Optional, Tuple

from appwrite.client import Client
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.query import Query
from appwrite.services.databases import Databases

from skoolplannr.config.settings import settings
from skoolplannr.core.grades import RULES_BY_CREDITS, evaluate_subject
from skoolplannr.core.gpa import calculate_cgpa, calculate_sgpa


class AppwriteServiceError(Exception):
    pass


class AppwriteService:
    def __init__(
        self,
        endpoint: str,
        project_id: str,
        api_key: str,
        database_id: str,
        users_collection_id: str,
        years_collection_id: str,
        terms_collection_id: str,
        subjects_collection_id: str,
        tasks_collection_id: str,
        events_collection_id: str,
        grades_collection_id: str,
        assessments_collection_id: str,
    ) -> None:
        if not endpoint:
            raise AppwriteServiceError("Missing APPWRITE_ENDPOINT in environment")
        if not project_id:
            raise AppwriteServiceError("Missing APPWRITE_PROJECT_ID in environment")
        if not api_key:
            raise AppwriteServiceError("Missing APPWRITE_API_KEY in environment")
        if not database_id:
            raise AppwriteServiceError("Missing APPWRITE_DATABASE_ID in environment")

        self.database_id = database_id
        self.users_collection_id = users_collection_id
        self.years_collection_id = years_collection_id
        self.terms_collection_id = terms_collection_id
        self.subjects_collection_id = subjects_collection_id
        self.tasks_collection_id = tasks_collection_id
        self.events_collection_id = events_collection_id
        self.grades_collection_id = grades_collection_id
        self.assessments_collection_id = assessments_collection_id

        client = Client()
        client.set_endpoint(endpoint.rstrip("/"))
        client.set_project(project_id)
        client.set_key(api_key)

        self.db = Databases(client)

    @classmethod
    def from_settings(cls) -> "AppwriteService":
        return cls(
            endpoint=settings.appwrite_endpoint,
            project_id=settings.appwrite_project_id,
            api_key=settings.appwrite_api_key,
            database_id=settings.appwrite_database_id,
            users_collection_id=settings.appwrite_users_collection_id,
            years_collection_id=settings.appwrite_years_collection_id,
            terms_collection_id=settings.appwrite_terms_collection_id,
            subjects_collection_id=settings.appwrite_subjects_collection_id,
            tasks_collection_id=settings.appwrite_tasks_collection_id,
            events_collection_id=settings.appwrite_events_collection_id,
            grades_collection_id=settings.appwrite_grades_collection_id,
            assessments_collection_id=settings.appwrite_assessments_collection_id,
        )

    @staticmethod
    def _to_iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _from_iso(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _list_documents(self, collection_id: str, queries: List[str]) -> List[Dict]:
        try:
            result = self.db.list_documents(self.database_id, collection_id, queries=queries)
            return list(result.get("documents", []))
        except AppwriteException as exc:
            raise AppwriteServiceError(str(exc)) from exc

    def _create_document(self, collection_id: str, data: Dict, document_id: Optional[str] = None) -> Dict:
        try:
            return self.db.create_document(
                self.database_id,
                collection_id,
                document_id or ID.unique(),
                data,
            )
        except AppwriteException as exc:
            raise AppwriteServiceError(str(exc)) from exc

    def _get_document(self, collection_id: str, document_id: str) -> Dict:
        try:
            return self.db.get_document(self.database_id, collection_id, document_id)
        except AppwriteException as exc:
            raise AppwriteServiceError(str(exc)) from exc

    def _update_document(self, collection_id: str, document_id: str, data: Dict) -> Dict:
        try:
            return self.db.update_document(self.database_id, collection_id, document_id, data)
        except AppwriteException as exc:
            raise AppwriteServiceError(str(exc)) from exc

    def _delete_document(self, collection_id: str, document_id: str) -> None:
        try:
            self.db.delete_document(self.database_id, collection_id, document_id)
        except AppwriteException as exc:
            raise AppwriteServiceError(str(exc)) from exc

    def _find_first(self, collection_id: str, queries: List[str]) -> Optional[Dict]:
        docs = self._list_documents(collection_id, [*queries, Query.limit(1)])
        if not docs:
            return None
        return docs[0]

    def ensure_user_profile(self, uid: str, email: str) -> None:
        profile = self.get_profile(uid)
        if profile:
            return
        self._create_document(
            self.users_collection_id,
            {
                "uid": uid,
                "email": email,
                "created_at": self._to_iso(datetime.now(timezone.utc)),
                "active_year_id": None,
                "active_term_id": None,
            },
            document_id=uid,
        )

    def get_profile(self, uid: str) -> Dict:
        try:
            return self.db.get_document(self.database_id, self.users_collection_id, uid)
        except AppwriteException as exc:
            if getattr(exc, "code", None) == 404:
                return {}
            raise AppwriteServiceError(str(exc)) from exc

    def has_onboarding(self, uid: str) -> bool:
        year = self._find_first(
            self.years_collection_id,
            [
                Query.equal("user_id", [uid]),
            ],
        )
        return year is not None

    def save_onboarding(
        self,
        uid: str,
        year_label: str,
        year_start: datetime,
        year_end: datetime,
        terms: List[Dict[str, datetime]],
    ) -> None:
        if not terms:
            raise AppwriteServiceError("At least one term is required.")

        year = self._create_document(
            self.years_collection_id,
            {
                "user_id": uid,
                "label": year_label,
                "start_date": self._to_iso(year_start),
                "end_date": self._to_iso(year_end),
                "created_date": self._to_iso(datetime.now(timezone.utc)),
            },
        )

        active_term_id: Optional[str] = None
        for index, term in enumerate(terms):
            created = self._create_document(
                self.terms_collection_id,
                {
                    "user_id": uid,
                    "year_id": year["$id"],
                    "name": term["name"],
                    "start_date": self._to_iso(term["start_date"]),
                    "end_date": self._to_iso(term["end_date"]),
                    "status": "active" if index == 0 else "upcoming",
                    "sgpa": None,
                    "total_credits": 0,
                },
            )
            if index == 0:
                active_term_id = created["$id"]

        self._update_document(
            self.users_collection_id,
            uid,
            {
                "active_year_id": year["$id"],
                "active_term_id": active_term_id,
            },
        )

    def _active_term(self, uid: str) -> Dict:
        profile = self.get_profile(uid)
        year_id = profile.get("active_year_id")
        term_id = profile.get("active_term_id")
        if not year_id or not term_id:
            raise AppwriteServiceError("Active academic year/term not set. Complete onboarding first.")

        term = self._find_first(
            self.terms_collection_id,
            [
                Query.equal("$id", [term_id]),
                Query.equal("year_id", [year_id]),
                Query.equal("user_id", [uid]),
            ],
        )
        if not term:
            raise AppwriteServiceError("Active term not found.")
        return term

    def list_years_and_terms(self, uid: str) -> List[Dict]:
        years = self._list_documents(
            self.years_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.order_asc("start_date"),
            ],
        )

        results: List[Dict] = []
        for year in years:
            terms = self._list_documents(
                self.terms_collection_id,
                [
                    Query.equal("user_id", [uid]),
                    Query.equal("year_id", [year["$id"]]),
                    Query.order_asc("start_date"),
                ],
            )
            results.append(
                {
                    "id": year["$id"],
                    "label": year.get("label", year["$id"]),
                    "start_date": self._from_iso(year.get("start_date")),
                    "terms": [
                        {
                            "id": term["$id"],
                            "name": term.get("name", term["$id"]),
                            "start_date": self._from_iso(term.get("start_date")),
                        }
                        for term in terms
                    ],
                }
            )

        return results

    def set_active_term(self, uid: str, year_id: str, term_id: str) -> None:
        self._update_document(
            self.users_collection_id,
            uid,
            {
                "active_year_id": year_id,
                "active_term_id": term_id,
            },
        )

    def list_subjects(self, uid: str) -> List[Dict]:
        active_term = self._active_term(uid)
        docs = self._list_documents(
            self.subjects_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.equal("term_id", [active_term["$id"]]),
            ],
        )

        results: List[Dict] = []
        for doc in docs:
            row = dict(doc)
            row["id"] = row["$id"]
            schedule_slots = row.get("scheduled_slots")
            if isinstance(schedule_slots, str) and schedule_slots:
                try:
                    row["schedule_slots"] = json.loads(schedule_slots)
                except ValueError:
                    row["schedule_slots"] = []
            elif isinstance(schedule_slots, list):
                row["schedule_slots"] = schedule_slots
            else:
                row["schedule_slots"] = []
            results.append(row)
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
        active_term = self._active_term(uid)
        doc = self._create_document(
            self.subjects_collection_id,
            {
                "user_id": uid,
                "year_id": active_term["year_id"],
                "term_id": active_term["$id"],
                "name": name,
                "instructor": instructor,
                "location": location,
                "credits": credits,
                "scheduled_slots": json.dumps(schedule_slots),
                "created_at": self._to_iso(datetime.now(timezone.utc)),
            },
        )
        return doc["$id"]

    def delete_subject(self, uid: str, subject_id: str) -> None:
        subject = self._find_first(
            self.subjects_collection_id,
            [
                Query.equal("$id", [subject_id]),
                Query.equal("user_id", [uid]),
            ],
        )
        if not subject:
            return
        self._delete_document(self.subjects_collection_id, subject_id)

    def list_tasks(self, uid: str, include_completed: bool = True) -> List[Dict]:
        active_term = self._active_term(uid)
        docs = self._list_documents(
            self.tasks_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.equal("term_id", [active_term["$id"]]),
            ],
        )

        results: List[Dict] = []
        for doc in docs:
            if not include_completed and bool(doc.get("completed")):
                continue
            row = dict(doc)
            row["id"] = row["$id"]
            results.append(row)

        results.sort(key=lambda row: row.get("due_at") or "9999-12-31T00:00:00+00:00")
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
        active_term = self._active_term(uid)
        doc = self._create_document(
            self.tasks_collection_id,
            {
                "user_id": uid,
                "year_id": active_term["year_id"],
                "term_id": active_term["$id"],
                "title": title,
                "description": description,
                "subject_id": subject_id,
                "task_type": task_type,
                "due_at": self._to_iso(due_at),
                "completed": False,
                "priority": priority,
                "created_at": self._to_iso(datetime.now(timezone.utc)),
            },
        )
        return doc["$id"]

    def set_task_completed(self, uid: str, task_id: str, completed: bool) -> None:
        task = self._find_first(
            self.tasks_collection_id,
            [
                Query.equal("$id", [task_id]),
                Query.equal("user_id", [uid]),
            ],
        )
        if not task:
            raise AppwriteServiceError("Task not found.")
        self._update_document(self.tasks_collection_id, task_id, {"completed": completed})

    def delete_task(self, uid: str, task_id: str) -> None:
        task = self._find_first(
            self.tasks_collection_id,
            [
                Query.equal("$id", [task_id]),
                Query.equal("user_id", [uid]),
            ],
        )
        if not task:
            return
        self._delete_document(self.tasks_collection_id, task_id)

    def list_events(self, uid: str) -> List[Dict]:
        active_term = self._active_term(uid)
        docs = self._list_documents(
            self.events_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.equal("term_id", [active_term["$id"]]),
            ],
        )

        results: List[Dict] = []
        for doc in docs:
            row = dict(doc)
            row["id"] = row["$id"]
            results.append(row)

        results.sort(key=lambda row: row.get("starts_at") or "9999-12-31T00:00:00+00:00")
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
        active_term = self._active_term(uid)
        doc = self._create_document(
            self.events_collection_id,
            {
                "user_id": uid,
                "year_id": active_term["year_id"],
                "term_id": active_term["$id"],
                "title": title,
                "event_type": event_type,
                "starts_at": self._to_iso(starts_at),
                "ends_at": self._to_iso(ends_at),
                "subject_id": subject_id,
                "created_at": self._to_iso(datetime.now(timezone.utc)),
            },
        )
        return doc["$id"]

    def delete_event(self, uid: str, event_id: str) -> None:
        event = self._find_first(
            self.events_collection_id,
            [
                Query.equal("$id", [event_id]),
                Query.equal("user_id", [uid]),
            ],
        )
        if not event:
            return
        self._delete_document(self.events_collection_id, event_id)

    def get_subject(self, uid: str, subject_id: str) -> Dict:
        subject = self._find_first(
            self.subjects_collection_id,
            [
                Query.equal("$id", [subject_id]),
                Query.equal("user_id", [uid]),
            ],
        )
        if not subject:
            return {}
        row = dict(subject)
        row["id"] = row["$id"]
        schedule_slots = row.get("scheduled_slots")
        if isinstance(schedule_slots, str) and schedule_slots:
            try:
                row["schedule_slots"] = json.loads(schedule_slots)
            except ValueError:
                row["schedule_slots"] = []
        elif isinstance(schedule_slots, list):
            row["schedule_slots"] = schedule_slots
        else:
            row["schedule_slots"] = []
        return row

    def get_assessments(self, uid: str, subject_id: str) -> Dict[str, float]:
        docs = self._list_documents(
            self.assessments_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.equal("subject_id", [subject_id]),
            ],
        )

        results: Dict[str, float] = {}
        for doc in docs:
            if "type" in doc and "score_raw" in doc:
                results[str(doc["type"])] = float(doc["score_raw"])
        return results

    def save_assessments_and_grade(self, uid: str, subject_id: str, raw_scores: Dict[str, float]) -> Dict:
        subject = self.get_subject(uid, subject_id)
        if not subject:
            raise AppwriteServiceError("Subject not found for grade input.")

        credits = int(subject.get("credits", 0))
        if credits not in RULES_BY_CREDITS:
            raise AppwriteServiceError("Unsupported credit model for subject.")

        rules = RULES_BY_CREDITS[credits]

        existing = self._list_documents(
            self.assessments_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.equal("subject_id", [subject_id]),
            ],
        )
        existing_by_type = {str(doc.get("type")): doc for doc in existing if doc.get("type") is not None}

        for name, rule in rules.items():
            if name in raw_scores:
                raw = float(raw_scores[name])
                weighted = (max(0.0, min(raw, rule.max_raw)) / rule.max_raw) * rule.reduced_to
                payload = {
                    "user_id": uid,
                    "subject_id": subject_id,
                    "type": name,
                    "max_raw": rule.max_raw,
                    "weight_to": rule.reduced_to,
                    "score_raw": raw,
                    "score_weighted": round(weighted, 2),
                }
                existing_doc = existing_by_type.get(name)
                if existing_doc:
                    self._update_document(self.assessments_collection_id, existing_doc["$id"], payload)
                else:
                    self._create_document(self.assessments_collection_id, payload)
            else:
                existing_doc = existing_by_type.get(name)
                if existing_doc:
                    self._delete_document(self.assessments_collection_id, existing_doc["$id"])

        missing = [name for name in rules if name not in raw_scores]
        existing_grade = self._find_first(
            self.grades_collection_id,
            [
                Query.equal("user_id", [uid]),
                Query.equal("subject_id", [subject_id]),
            ],
        )
        if missing:
            if existing_grade:
                self._delete_document(self.grades_collection_id, existing_grade["$id"])
            return {
                "partial": True,
                "missing": missing,
                "subject_id": subject_id,
            }

        final_score, letter_grade, grade_point = evaluate_subject(credits, raw_scores)
        grade_doc = {
            "partial": False,
            "user_id": uid,
            "subject_id": subject_id,
            "subject_name": subject.get("name", ""),
            "credits": credits,
            "final_score_100": final_score,
            "letter_grade": letter_grade,
            "grade_point": grade_point,
            "updated_at": self._to_iso(datetime.now(timezone.utc)),
        }

        if existing_grade:
            self._update_document(self.grades_collection_id, existing_grade["$id"], grade_doc)
        else:
            self._create_document(self.grades_collection_id, grade_doc)

        return grade_doc

    def list_grades(self, uid: str) -> List[Dict]:
        docs = self._list_documents(
            self.grades_collection_id,
            [
                Query.equal("user_id", [uid]),
            ],
        )

        results: List[Dict] = []
        for doc in docs:
            row = dict(doc)
            row["id"] = row["$id"]
            results.append(row)
        results.sort(key=lambda row: row.get("subject_name", ""))
        return results

    def calculate_and_store_sgpa(self, uid: str) -> Tuple[float, int]:
        grades = self.list_grades(uid)
        if not grades:
            raise AppwriteServiceError("No grades found to calculate SGPA.")

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

        active_term = self._active_term(uid)
        self._update_document(
            self.terms_collection_id,
            active_term["$id"],
            {"sgpa": sgpa, "total_credits": total_credits},
        )
        return sgpa, total_credits

    def calculate_and_store_cgpa(self, uid: str) -> Tuple[float, List[Dict]]:
        years = self._list_documents(
            self.years_collection_id,
            [
                Query.equal("user_id", [uid]),
            ],
        )

        semester_results = []
        trend: List[Dict] = []
        for year in years:
            year_label = year.get("label", year["$id"])
            terms = self._list_documents(
                self.terms_collection_id,
                [
                    Query.equal("user_id", [uid]),
                    Query.equal("year_id", [year["$id"]]),
                ],
            )
            for term in terms:
                sgpa = term.get("sgpa")
                credits = term.get("total_credits")
                if sgpa is None or not credits:
                    continue
                semester_results.append((float(sgpa), int(credits)))
                trend.append(
                    {
                        "label": f"{year_label} - {term.get('name', term['$id'])}",
                        "sgpa": float(sgpa),
                        "credits": int(credits),
                    }
                )

        if not semester_results:
            raise AppwriteServiceError("No semester results found for CGPA.")

        cgpa = calculate_cgpa(semester_results)
        self._update_document(self.users_collection_id, uid, {"cgpa": cgpa})
        return cgpa, trend

    def get_cached_cgpa(self, uid: str) -> Optional[float]:
        profile = self.get_profile(uid)
        value = profile.get("cgpa")
        if value is None:
            return None
        return float(value)

    def get_active_term_summary(self, uid: str) -> Dict:
        term = self._active_term(uid)
        return term
