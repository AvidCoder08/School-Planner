from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from skoolplannr.services.auth_service import AuthServiceError, FirebaseAuthService
from skoolplannr.services.firestore_service import FirestoreService, FirestoreServiceError


app = FastAPI(title="SkoolPlannr API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthPayload(BaseModel):
    email: str
    password: str


class TermPayload(BaseModel):
    name: str
    start_date: datetime
    end_date: datetime


class OnboardingPayload(BaseModel):
    year_label: str
    year_start: datetime
    year_end: datetime
    terms: List[TermPayload]


class SubjectPayload(BaseModel):
    name: str
    instructor: str = ""
    location: str = ""
    credits: int = Field(ge=1)
    schedule_slots: List[Dict[str, str]] = Field(default_factory=list)


class TaskPayload(BaseModel):
    title: str
    description: str = ""
    subject_id: Optional[str] = None
    task_type: str
    due_at: datetime
    priority: str


class TaskCompletionPayload(BaseModel):
    completed: bool


class EventPayload(BaseModel):
    title: str
    event_type: str
    starts_at: datetime
    ends_at: datetime
    subject_id: Optional[str] = None


class GradePayload(BaseModel):
    raw_scores: Dict[str, float]


def _required_uid(x_user_id: Optional[str]) -> str:
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing x-user-id header")
    return x_user_id


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/signup")
def sign_up(payload: AuthPayload) -> Dict:
    auth = FirebaseAuthService.from_settings()
    fs = FirestoreService.from_settings()
    try:
        result = auth.sign_up(payload.email, payload.password)
        fs.ensure_user_profile(result.uid, result.email)
        return {
            "uid": result.uid,
            "email": result.email,
            "id_token": result.id_token,
            "refresh_token": result.refresh_token,
        }
    except AuthServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.post("/auth/login")
def login(payload: AuthPayload) -> Dict:
    auth = FirebaseAuthService.from_settings()
    try:
        result = auth.sign_in(payload.email, payload.password)
        return {
            "uid": result.uid,
            "email": result.email,
            "id_token": result.id_token,
            "refresh_token": result.refresh_token,
        }
    except AuthServiceError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@app.get("/profile")
def get_profile(x_user_id: Optional[str] = Header(default=None)) -> Dict:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        profile = fs.get_profile(uid)
        return {
            "uid": uid,
            "profile": profile,
            "has_onboarding": fs.has_onboarding(uid),
        }
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/onboarding")
def save_onboarding(payload: OnboardingPayload, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        fs.save_onboarding(
            uid=uid,
            year_label=payload.year_label,
            year_start=payload.year_start,
            year_end=payload.year_end,
            terms=[term.model_dump() for term in payload.terms],
        )
        return {"status": "saved"}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/subjects")
def list_subjects(x_user_id: Optional[str] = Header(default=None)) -> List[Dict]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        return fs.list_subjects(uid)
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/subjects")
def create_subject(payload: SubjectPayload, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        subject_id = fs.create_subject(uid, **payload.model_dump())
        return {"id": subject_id}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: str, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        fs.delete_subject(uid, subject_id)
        return {"status": "deleted"}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/tasks")
def list_tasks(
    include_completed: bool = True,
    x_user_id: Optional[str] = Header(default=None),
) -> List[Dict]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        return fs.list_tasks(uid, include_completed=include_completed)
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/tasks")
def create_task(payload: TaskPayload, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        task_id = fs.create_task(uid, **payload.model_dump())
        return {"id": task_id}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.patch("/tasks/{task_id}/completed")
def set_task_completed(
    task_id: str,
    payload: TaskCompletionPayload,
    x_user_id: Optional[str] = Header(default=None),
) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        fs.set_task_completed(uid, task_id, payload.completed)
        return {"status": "updated"}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        fs.delete_task(uid, task_id)
        return {"status": "deleted"}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/events")
def list_events(x_user_id: Optional[str] = Header(default=None)) -> List[Dict]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        return fs.list_events(uid)
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/events")
def create_event(payload: EventPayload, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        event_id = fs.create_event(uid, **payload.model_dump())
        return {"id": event_id}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.delete("/events/{event_id}")
def delete_event(event_id: str, x_user_id: Optional[str] = Header(default=None)) -> Dict[str, str]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        fs.delete_event(uid, event_id)
        return {"status": "deleted"}
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.get("/grades")
def list_grades(x_user_id: Optional[str] = Header(default=None)) -> List[Dict]:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        return fs.list_grades(uid)
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.post("/grades/{subject_id}")
def save_grade(subject_id: str, payload: GradePayload, x_user_id: Optional[str] = Header(default=None)) -> Dict:
    uid = _required_uid(x_user_id)
    fs = FirestoreService.from_settings()
    try:
        return fs.save_assessments_and_grade(uid, subject_id, payload.raw_scores)
    except FirestoreServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
