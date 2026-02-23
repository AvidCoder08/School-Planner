# Appwrite Function Backend

This function replaces the FastAPI backend for production.

## What it exposes

The function serves the same API routes used by Flutter:

- `GET /health`
- `POST /auth/signup`
- `POST /auth/login`
- `GET /profile`
- `POST /onboarding`
- `GET /subjects`
- `POST /subjects`
- `DELETE /subjects/{subject_id}`
- `GET /tasks`
- `POST /tasks`
- `PATCH /tasks/{task_id}/completed`
- `DELETE /tasks/{task_id}`
- `GET /events`
- `POST /events`
- `DELETE /events/{event_id}`
- `GET /grades`
- `POST /grades/{subject_id}`
- `POST /attendance/pesu`

## Function setup in Appwrite Console

1. Go to **Functions → Create function**.
2. Runtime: **Python**.
3. Root directory: repository root.
4. Entrypoint: `appwrite/functions/backend/main.py`.
5. Build command: `pip install -r appwrite/functions/backend/requirements.txt`.
6. In **Execute access**, allow the clients you need (for domain calls, use `Any`).
7. In **Domains**, use the generated Appwrite global domain (or add a custom domain).

## Environment variables

Set these in Function settings:

- `APPWRITE_ENDPOINT=https://sgp.cloud.appwrite.io/v1`
- `APPWRITE_PROJECT_ID=699c792c002591020870`
- `APPWRITE_DATABASE_ID=<database_id>`
- `APPWRITE_USERS_COLLECTION_ID=users`
- `APPWRITE_YEARS_COLLECTION_ID=academic_years`
- `APPWRITE_TERMS_COLLECTION_ID=terms`
- `APPWRITE_SUBJECTS_COLLECTION_ID=subjects`
- `APPWRITE_TASKS_COLLECTION_ID=tasks`
- `APPWRITE_EVENTS_COLLECTION_ID=events`
- `APPWRITE_GRADES_COLLECTION_ID=grades`
- `APPWRITE_ASSESSMENTS_COLLECTION_ID=assessments`
- `CORS_ALLOWED_ORIGINS=https://<your-web-domain>,http://localhost:5173,http://127.0.0.1:5173`
- `CORS_ALLOW_ORIGIN_REGEX=^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$`

Notes:
- You do **not** need to set `APPWRITE_API_KEY` for this function if dynamic keys are enabled (the code uses `APPWRITE_FUNCTION_API_KEY` fallback).
- Set `APPWRITE_FUNCTION_DEBUG=true` temporarily only for debugging.

## Required function scopes

Grant the function enough scopes to read/write Appwrite Databases and use account/session APIs as used by this backend.

## Flutter wiring

Set Flutter API base URL to your function domain:

- Web build:
  - `flutter build web --release --dart-define=API_BASE_URL=https://<function-domain>`
- Android build:
  - `flutter build appbundle --release --dart-define=API_BASE_URL=https://<function-domain>`

The Flutter app can continue using `/auth/login`, `/subjects`, etc.
