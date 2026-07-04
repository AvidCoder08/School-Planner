"""Firebase integration placeholder.

This project currently ships with SQLite-backed local storage for a runnable baseline.
To move to Firebase, replace Storage calls in ui/app.py with this service methods.
"""

from __future__ import annotations

import os


class FirebaseConfigError(RuntimeError):
    pass


def ensure_firebase_env() -> None:
    required = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_PRIVATE_KEY",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise FirebaseConfigError(f"Missing Firebase env vars: {', '.join(missing)}")
