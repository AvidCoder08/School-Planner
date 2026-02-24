import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs

def _src_dir_from_settings_file(settings_file: Path) -> Optional[Path]:
    try:
        if settings_file.name == "settings.py" and settings_file.parent.name == "config":
            package_dir = settings_file.parent.parent
            if package_dir.name == "skoolplannr":
                return package_dir.parent
    except Exception:
        return None
    return None


def _find_src_dir(start_file: Path) -> Optional[Path]:
    env_src = os.getenv("SKOOLPLANNR_SRC_DIR", "").strip()
    if env_src:
        env_path = Path(env_src)
        if (env_path / "skoolplannr" / "config" / "settings.py").exists():
            return env_path

    for parent in (start_file.parent, *start_file.parents):
        if (parent / "skoolplannr" / "config" / "settings.py").exists():
            return parent

        candidate = parent / "src"
        if (candidate / "skoolplannr").exists():
            return candidate

    for root in (start_file.parent, *start_file.parents):
        try:
            for settings_file in root.glob("**/skoolplannr/config/settings.py"):
                src_dir = _src_dir_from_settings_file(settings_file)
                if src_dir is not None:
                    return src_dir
        except Exception:
            continue

    return None


SRC_DIR = _find_src_dir(Path(__file__).resolve())
if SRC_DIR is None:
    raise RuntimeError(
        "Could not locate src/skoolplannr. Set Appwrite Function root to repository root, "
        "entrypoint to appwrite/functions/backend/main.py, and build command to "
        "pip install -r appwrite/functions/backend/requirements.txt"
    )

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from skoolplannr.config.settings import settings
from skoolplannr.services.appwrite_service import AppwriteService, AppwriteServiceError
from skoolplannr.services.auth_service import AppwriteAuthService, AuthServiceError
from skoolplannr.services.pesu_service import PesuService, PesuServiceError


LOCAL_REGEX = r"^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$"


class HttpError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _headers(req: Any) -> Dict[str, str]:
    raw_headers = getattr(req, "headers", {}) or {}
    return {str(key).lower(): str(value) for key, value in raw_headers.items()}


def _normalize_path(req: Any) -> str:
    path = str(getattr(req, "path", "") or "/")
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


def _cors_headers(req: Any) -> Dict[str, str]:
    req_headers = _headers(req)
    origin = req_headers.get("origin", "")
    if not origin:
        return {}

    if origin in settings.cors_allowed_origins:
        allowed_origin = origin
    else:
        regex = settings.cors_allow_origin_regex or LOCAL_REGEX
        allowed_origin = origin if re.match(regex, origin) else ""

    if not allowed_origin:
        return {}

    return {
        "access-control-allow-origin": allowed_origin,
        "access-control-allow-credentials": "true",
        "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
        "access-control-allow-headers": "Content-Type,Authorization,x-user-id,x-appwrite-user-jwt",
        "vary": "Origin",
    }


def _json_response(context: Any, payload: Any, status_code: int = 200, req: Any = None):
    headers = _cors_headers(req) if req is not None else {}
    return context.res.json(payload, status_code, headers)


def _empty_response(context: Any, status_code: int = 204, req: Any = None):
    headers = _cors_headers(req) if req is not None else {}
    return context.res.empty(status_code, headers)


def _parse_body(req: Any) -> Dict[str, Any]:
    def _from_candidate(candidate: Any) -> Optional[Dict[str, Any]]:
        if candidate is None:
            return None

        if isinstance(candidate, (bytes, bytearray)):
            candidate = candidate.decode("utf-8", errors="ignore")

        if isinstance(candidate, str):
            text = candidate.strip()
            if not text:
                return None
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed_qs = parse_qs(text, keep_blank_values=True)
                if parsed_qs:
                    return {k: (v[-1] if isinstance(v, list) and v else "") for k, v in parsed_qs.items()}
                return None
            candidate = parsed

        if isinstance(candidate, dict):
            if "body" in candidate:
                nested = _from_candidate(candidate.get("body"))
                if nested is not None:
                    return nested

            if "bodyJson" in candidate and isinstance(candidate.get("bodyJson"), dict):
                return candidate.get("bodyJson")

            return candidate

        return None

    for attr in ("bodyJson", "body", "bodyText", "payload", "rawBody"):
        parsed = _from_candidate(getattr(req, attr, None))
        if parsed is not None:
            return parsed

    return {}


def _require_user_id(req: Any) -> str:
    value = _headers(req).get("x-user-id", "").strip()
    if not value:
        raise HttpError(401, "Missing x-user-id header")
    return value


def _parse_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise HttpError(400, f"{field_name} must be an ISO-8601 datetime string")

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise HttpError(400, f"Invalid datetime for {field_name}") from exc


def _to_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on"}:
        return True
    if text in {"false", "0", "no", "n", "off"}:
        return False
    return default


def _run_async(coro):
    return asyncio.run(coro)


def _auth_signup(req: Any) -> Dict[str, Any]:
    payload = _parse_body(req)
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))
    name = payload.get("name")

    if not email or not password:
        raise HttpError(400, "email and password are required")

    try:
        auth = AppwriteAuthService.from_settings()
        db = AppwriteService.from_settings()
        result = auth.sign_up(email, password, str(name).strip() if isinstance(name, str) else None)
        db.ensure_user_profile(result.uid, result.email)
        return {
            "uid": result.uid,
            "email": result.email,
            "id_token": result.id_token,
            "refresh_token": result.refresh_token,
        }
    except AuthServiceError as exc:
        raise HttpError(400, str(exc)) from exc
    except AppwriteServiceError as exc:
        raise HttpError(500, str(exc)) from exc


def _auth_login(req: Any) -> Dict[str, Any]:
    payload = _parse_body(req)
    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))
    if not email or not password:
        raise HttpError(400, "email and password are required")

    try:
        auth = AppwriteAuthService.from_settings()
        result = auth.sign_in(email, password)
        return {
            "uid": result.uid,
            "email": result.email,
            "id_token": result.id_token,
            "refresh_token": result.refresh_token,
        }
    except AuthServiceError as exc:
        raise HttpError(401, str(exc)) from exc


def _get_profile(req: Any) -> Dict[str, Any]:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        profile = fs.get_profile(uid)
        return {
            "uid": uid,
            "profile": profile,
            "has_onboarding": fs.has_onboarding(uid),
        }
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _save_onboarding(req: Any) -> Dict[str, Any]:
    uid = _require_user_id(req)
    payload = _parse_body(req)

    year_label = str(payload.get("year_label", "")).strip()
    year_start = _parse_datetime(payload.get("year_start"), "year_start")
    year_end = _parse_datetime(payload.get("year_end"), "year_end")

    terms_payload = payload.get("terms", [])
    if not isinstance(terms_payload, list):
        raise HttpError(400, "terms must be an array")

    terms = []
    for idx, term in enumerate(terms_payload):
        if not isinstance(term, dict):
            raise HttpError(400, f"terms[{idx}] must be an object")
        name = str(term.get("name", "")).strip()
        if not name:
            raise HttpError(400, f"terms[{idx}].name is required")
        terms.append(
            {
                "name": name,
                "start_date": _parse_datetime(term.get("start_date"), f"terms[{idx}].start_date"),
                "end_date": _parse_datetime(term.get("end_date"), f"terms[{idx}].end_date"),
            }
        )

    fs = AppwriteService.from_settings()
    try:
        fs.save_onboarding(
            uid=uid,
            year_label=year_label,
            year_start=year_start,
            year_end=year_end,
            terms=terms,
        )
        return {"status": "saved"}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _list_subjects(req: Any) -> Any:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        return fs.list_subjects(uid)
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _create_subject(req: Any) -> Dict[str, Any]:
    uid = _require_user_id(req)
    payload = _parse_body(req)

    name = str(payload.get("name", "")).strip()
    credits = payload.get("credits")
    if not name:
        raise HttpError(400, "name is required")
    if not isinstance(credits, int) or credits < 1:
        raise HttpError(400, "credits must be an integer >= 1")

    schedule_slots = payload.get("schedule_slots", [])
    if not isinstance(schedule_slots, list):
        raise HttpError(400, "schedule_slots must be an array")

    fs = AppwriteService.from_settings()
    try:
        subject_id = fs.create_subject(
            uid,
            name=name,
            instructor=str(payload.get("instructor", "")),
            location=str(payload.get("location", "")),
            credits=credits,
            schedule_slots=schedule_slots,
        )
        return {"id": subject_id}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _delete_subject(req: Any, subject_id: str) -> Dict[str, Any]:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        fs.delete_subject(uid, subject_id)
        return {"status": "deleted"}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _list_tasks(req: Any) -> Any:
    uid = _require_user_id(req)
    include_completed = _to_bool(getattr(req, "query", {}).get("include_completed"), default=True)
    fs = AppwriteService.from_settings()
    try:
        return fs.list_tasks(uid, include_completed=include_completed)
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _create_task(req: Any) -> Dict[str, Any]:
    uid = _require_user_id(req)
    payload = _parse_body(req)

    title = str(payload.get("title", "")).strip()
    task_type = str(payload.get("task_type", "")).strip()
    priority = str(payload.get("priority", "")).strip()

    if not title:
        raise HttpError(400, "title is required")
    if not task_type:
        raise HttpError(400, "task_type is required")
    if not priority:
        raise HttpError(400, "priority is required")

    due_at = _parse_datetime(payload.get("due_at"), "due_at")

    subject_id = payload.get("subject_id")
    if subject_id is not None:
        subject_id = str(subject_id).strip() or None

    fs = AppwriteService.from_settings()
    try:
        task_id = fs.create_task(
            uid,
            title=title,
            description=str(payload.get("description", "")),
            subject_id=subject_id,
            task_type=task_type,
            due_at=due_at,
            priority=priority,
        )
        return {"id": task_id}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _set_task_completed(req: Any, task_id: str) -> Dict[str, Any]:
    uid = _require_user_id(req)
    payload = _parse_body(req)
    if "completed" not in payload:
        raise HttpError(400, "completed is required")

    completed = _to_bool(payload.get("completed"), default=False)

    fs = AppwriteService.from_settings()
    try:
        fs.set_task_completed(uid, task_id, completed)
        return {"status": "updated"}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _delete_task(req: Any, task_id: str) -> Dict[str, Any]:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        fs.delete_task(uid, task_id)
        return {"status": "deleted"}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _list_events(req: Any) -> Any:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        return fs.list_events(uid)
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _create_event(req: Any) -> Dict[str, Any]:
    uid = _require_user_id(req)
    payload = _parse_body(req)

    title = str(payload.get("title", "")).strip()
    event_type = str(payload.get("event_type", "")).strip()
    if not title:
        raise HttpError(400, "title is required")
    if not event_type:
        raise HttpError(400, "event_type is required")

    starts_at = _parse_datetime(payload.get("starts_at"), "starts_at")
    ends_at = _parse_datetime(payload.get("ends_at"), "ends_at")

    subject_id = payload.get("subject_id")
    if subject_id is not None:
        subject_id = str(subject_id).strip() or None

    fs = AppwriteService.from_settings()
    try:
        event_id = fs.create_event(
            uid,
            title=title,
            event_type=event_type,
            starts_at=starts_at,
            ends_at=ends_at,
            subject_id=subject_id,
        )
        return {"id": event_id}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _delete_event(req: Any, event_id: str) -> Dict[str, Any]:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        fs.delete_event(uid, event_id)
        return {"status": "deleted"}
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _list_grades(req: Any) -> Any:
    uid = _require_user_id(req)
    fs = AppwriteService.from_settings()
    try:
        return fs.list_grades(uid)
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _save_grade(req: Any, subject_id: str) -> Dict[str, Any]:
    uid = _require_user_id(req)
    payload = _parse_body(req)
    raw_scores = payload.get("raw_scores")
    if not isinstance(raw_scores, dict):
        raise HttpError(400, "raw_scores must be an object")

    normalized_scores: Dict[str, float] = {}
    for key, value in raw_scores.items():
        try:
            normalized_scores[str(key)] = float(value)
        except (TypeError, ValueError) as exc:
            raise HttpError(400, f"Invalid score for {key}") from exc

    fs = AppwriteService.from_settings()
    try:
        return fs.save_assessments_and_grade(uid, subject_id, normalized_scores)
    except AppwriteServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _fetch_pesu_attendance(req: Any) -> Dict[str, Any]:
    _require_user_id(req)
    payload = _parse_body(req)

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    semester = payload.get("semester")
    if semester is not None:
        try:
            semester = int(semester)
        except (TypeError, ValueError) as exc:
            raise HttpError(400, "semester must be an integer") from exc

    service = PesuService()
    try:
        return _run_async(
            service.get_attendance(
                username=username,
                password=password,
                semester=semester,
            )
        )
    except PesuServiceError as exc:
        raise HttpError(400, str(exc)) from exc


def _route(context: Any, req: Any):
    method = str(getattr(req, "method", "GET") or "GET").upper()
    path = _normalize_path(req)

    if method == "OPTIONS":
        return _empty_response(context, 204, req=req)

    if method == "GET" and path == "/health":
        return _json_response(context, {"status": "ok"}, req=req)

    if method == "POST" and path == "/auth/signup":
        return _json_response(context, _auth_signup(req), req=req)

    if method == "POST" and path == "/auth/login":
        return _json_response(context, _auth_login(req), req=req)

    if method == "GET" and path == "/profile":
        return _json_response(context, _get_profile(req), req=req)

    if method == "POST" and path == "/onboarding":
        return _json_response(context, _save_onboarding(req), req=req)

    if method == "GET" and path == "/subjects":
        return _json_response(context, _list_subjects(req), req=req)

    if method == "POST" and path == "/subjects":
        return _json_response(context, _create_subject(req), req=req)

    subject_match = re.fullmatch(r"/subjects/([^/]+)", path)
    if method == "DELETE" and subject_match:
        return _json_response(context, _delete_subject(req, subject_match.group(1)), req=req)

    if method == "GET" and path == "/tasks":
        return _json_response(context, _list_tasks(req), req=req)

    if method == "POST" and path == "/tasks":
        return _json_response(context, _create_task(req), req=req)

    task_completed_match = re.fullmatch(r"/tasks/([^/]+)/completed", path)
    if method == "PATCH" and task_completed_match:
        return _json_response(context, _set_task_completed(req, task_completed_match.group(1)), req=req)

    task_match = re.fullmatch(r"/tasks/([^/]+)", path)
    if method == "DELETE" and task_match:
        return _json_response(context, _delete_task(req, task_match.group(1)), req=req)

    if method == "GET" and path == "/events":
        return _json_response(context, _list_events(req), req=req)

    if method == "POST" and path == "/events":
        return _json_response(context, _create_event(req), req=req)

    event_match = re.fullmatch(r"/events/([^/]+)", path)
    if method == "DELETE" and event_match:
        return _json_response(context, _delete_event(req, event_match.group(1)), req=req)

    if method == "GET" and path == "/grades":
        return _json_response(context, _list_grades(req), req=req)

    grade_match = re.fullmatch(r"/grades/([^/]+)", path)
    if method == "POST" and grade_match:
        return _json_response(context, _save_grade(req, grade_match.group(1)), req=req)

    if method == "POST" and path == "/attendance/pesu":
        return _json_response(context, _fetch_pesu_attendance(req), req=req)

    raise HttpError(404, "Not found")


def main(context: Any):
    req = context.req

    try:
        return _route(context, req)
    except HttpError as exc:
        return _json_response(context, {"detail": exc.detail}, status_code=exc.status_code, req=req)
    except Exception as exc:
        if os.getenv("APPWRITE_FUNCTION_DEBUG", "false").lower() == "true":
            context.error(str(exc))
            return _json_response(context, {"detail": str(exc)}, status_code=500, req=req)

        context.error("Unhandled exception in backend function")
        return _json_response(context, {"detail": "INTERNAL_SERVER_ERROR"}, status_code=500, req=req)
