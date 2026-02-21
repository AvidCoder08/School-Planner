from dataclasses import dataclass
from typing import Any, Dict
import requests

from skoolplannr.config.settings import settings


class AuthServiceError(Exception):
    pass


@dataclass
class AuthResult:
    uid: str
    email: str
    id_token: str
    refresh_token: str


class FirebaseAuthService:
    BASE_URL = "https://identitytoolkit.googleapis.com/v1"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise AuthServiceError("Missing FIREBASE_API_KEY in environment")
        self.api_key = api_key

    @classmethod
    def from_settings(cls) -> "FirebaseAuthService":
        return cls(settings.firebase_api_key)

    def sign_up(self, email: str, password: str) -> AuthResult:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        response = self._post("accounts:signUp", payload)
        return self._to_result(response)

    def sign_in(self, email: str, password: str) -> AuthResult:
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        }
        response = self._post("accounts:signInWithPassword", payload)
        return self._to_result(response)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{path}?key={self.api_key}"
        res = requests.post(url, json=payload, timeout=15)
        data = res.json()

        if res.status_code >= 400:
            error_key = data.get("error", {}).get("message", "AUTH_ERROR")
            raise AuthServiceError(error_key)

        return data

    @staticmethod
    def _to_result(data: Dict[str, Any]) -> AuthResult:
        return AuthResult(
            uid=data["localId"],
            email=data["email"],
            id_token=data["idToken"],
            refresh_token=data["refreshToken"],
        )
