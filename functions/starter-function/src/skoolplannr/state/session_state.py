from dataclasses import dataclass
from typing import Optional


@dataclass
class SessionState:
    uid: Optional[str] = None
    email: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return bool(self.uid and self.id_token)

    def clear(self) -> None:
        self.uid = None
        self.email = None
        self.id_token = None
        self.refresh_token = None
