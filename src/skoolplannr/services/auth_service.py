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
    email_verified: bool


class AppwriteAuthService:
    SIGN_UP_PATH = "/account"
    LOGIN_PATH = "/account/sessions/email"
    ACCOUNT_PATH = "/account"
    EMAIL_VERIFICATION_PATH = "/account/verification"

    def __init__(self, endpoint: str, project_id: str, api_key: str = "") -> None:
        if not endpoint:
            raise AuthServiceError("Missing APPWRITE_ENDPOINT in environment")
        if not project_id:
            raise AuthServiceError("Missing APPWRITE_PROJECT_ID in environment")
        self.endpoint = endpoint.rstrip("/")
        self.project_id = project_id
        self.api_key = api_key.strip()

    @classmethod
    def from_settings(cls) -> "AppwriteAuthService":
        return cls(
            settings.appwrite_endpoint,
            settings.appwrite_project_id,
            settings.appwrite_api_key,
        )

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
        session_secret = str(response.get("secret") or "")
        account = self.get_account(session_secret)
        return self._to_result(response, email, account)

    def get_account(self, session_secret: str) -> Dict[str, Any]:
        if not session_secret:
            raise AuthServiceError("INVALID_APPWRITE_SESSION")
        return self._get(self.ACCOUNT_PATH, session_secret=session_secret)

    def send_email_verification(self, session_secret: str, url: str) -> None:
        if not url.strip():
            raise AuthServiceError("VERIFICATION_URL_REQUIRED")
        self._post(
            self.EMAIL_VERIFICATION_PATH,
            {"url": url.strip()},
            session_secret=session_secret,
        )

    def complete_email_verification(
        self,
        session_secret: str,
        user_id: str,
        secret: str,
    ) -> Dict[str, Any]:
        if not user_id.strip() or not secret.strip():
            raise AuthServiceError("VERIFICATION_SECRET_REQUIRED")
        return self._put(
            self.EMAIL_VERIFICATION_PATH,
            {"userId": user_id.strip(), "secret": secret.strip()},
            session_secret=session_secret,
        )

    def _base_headers(self, session_secret: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-Appwrite-Project": self.project_id,
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["X-Appwrite-Key"] = self.api_key
        if session_secret:
            headers["X-Appwrite-Session"] = session_secret
        return headers

    def _get(self, path: str, session_secret: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        try:
            res = requests.get(
                url,
                headers=self._base_headers(session_secret=session_secret),
                timeout=15,
            )
        except RequestException as exc:
            raise AuthServiceError("AUTH_SERVICE_UNAVAILABLE") from exc
        return self._decode_response(res)

    def _post(
        self,
        path: str,
        payload: Dict[str, Any],
        session_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        try:
            res = requests.post(
                url,
                headers=self._base_headers(session_secret=session_secret),
                json=payload,
                timeout=15,
            )
        except RequestException as exc:
            raise AuthServiceError("AUTH_SERVICE_UNAVAILABLE") from exc
        return self._decode_response(res)

    def _put(
        self,
        path: str,
        payload: Dict[str, Any],
        session_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        try:
            res = requests.put(
                url,
                headers=self._base_headers(session_secret=session_secret),
                json=payload,
                timeout=15,
            )
        except RequestException as exc:
            raise AuthServiceError("AUTH_SERVICE_UNAVAILABLE") from exc
        return self._decode_response(res)

    @staticmethod
    def _decode_response(res: requests.Response) -> Dict[str, Any]:
        try:
            data = res.json()
        except ValueError:
            raise AuthServiceError("AUTH_SERVICE_UNAVAILABLE")

        if res.status_code >= 400:
            error_key = str(data.get("message") or data.get("type") or "AUTH_ERROR")
            raise AuthServiceError(error_key)

        return data

    @staticmethod
    def _to_result(data: Dict[str, Any], email: str, account: Dict[str, Any]) -> AuthResult:
        session_id = str(data.get("$id") or "")
        session_secret = str(data.get("secret") or "")
        uid = str(data.get("userId") or "")
        if not uid or not session_secret:
            raise AuthServiceError(
                "INVALID_APPWRITE_SESSION: Missing session secret. "
                "Ensure APPWRITE_FUNCTION_API_KEY (or APPWRITE_API_KEY) is configured."
            )
        return AuthResult(
            uid=uid,
            email=str(account.get("email") or email),
            id_token=session_secret,
            refresh_token=session_id,
            email_verified=account.get("emailVerification") is True,
        )
