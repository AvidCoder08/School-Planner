from dataclasses import dataclass
from typing import Any, Dict, Optional
import requests
from requests import RequestException

from skoolplannr.config.settings import settings


class AuthServiceError(Exception):
    pass


@dataclass
class AuthResult:
    uid: str
    email: str
    id_token: str
    refresh_token: str


class AppwriteAuthService:
    SIGN_UP_PATH = "/account"
    LOGIN_PATH = "/account/sessions/email"

    def __init__(self, endpoint: str, project_id: str) -> None:
        if not endpoint:
            raise AuthServiceError("Missing APPWRITE_ENDPOINT in environment")
        if not project_id:
            raise AuthServiceError("Missing APPWRITE_PROJECT_ID in environment")
        self.endpoint = endpoint.rstrip("/")
        self.project_id = project_id

    @classmethod
    def from_settings(cls) -> "AppwriteAuthService":
        return cls(settings.appwrite_endpoint, settings.appwrite_project_id)

    def sign_up(self, email: str, password: str, name: Optional[str] = None) -> AuthResult:
        payload = {
            "userId": "unique()",
            "email": email,
            "password": password,
        }
        if name and name.strip():
            payload["name"] = name.strip()
        self._post(self.SIGN_UP_PATH, payload)
        return self.sign_in(email, password)

    def sign_in(self, email: str, password: str) -> AuthResult:
        payload = {
            "email": email,
            "password": password,
        }
        response = self._post(self.LOGIN_PATH, payload)
        return self._to_result(response, email)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        headers = {
            "X-Appwrite-Project": self.project_id,
            "Content-Type": "application/json",
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=15)
        except RequestException as exc:
            raise AuthServiceError("AUTH_SERVICE_UNAVAILABLE") from exc
        try:
            data = res.json()
        except ValueError:
            raise AuthServiceError("AUTH_SERVICE_UNAVAILABLE")

        if res.status_code >= 400:
            error_key = str(data.get("message") or data.get("type") or "AUTH_ERROR")
            raise AuthServiceError(error_key)

        return data

    @staticmethod
    def _to_result(data: Dict[str, Any], email: str) -> AuthResult:
        session_id = str(data.get("$id") or "")
        session_secret = str(data.get("secret") or "")
        uid = str(data.get("userId") or "")
        if not uid:
            raise AuthServiceError("INVALID_APPWRITE_SESSION")
        return AuthResult(
            uid=uid,
            email=email,
            id_token=session_secret,
            refresh_token=session_id,
        )
