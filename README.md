# School-Planner (SkoolPlannr / AcademaSync)

Monorepo for a student planner and grade tracker.

Current active stack:
- Flutter frontend (`frontend/flutter`)
- FastAPI backend (`src/skoolplannr`)
- Appwrite (auth + database + function deployment)

Legacy prototype code from an earlier Flet/Firebase baseline still exists in `app/` and `docs/PROJECT_SPEC.md`.

## Repository layout

- `frontend/flutter` - Flutter client (web/desktop/mobile)
- `src/skoolplannr` - FastAPI API + Appwrite integrations
- `appwrite/functions/backend` - Appwrite Function entrypoint that serves the API
- `tests` - grading and GPA unit tests
- `run.bat` - Windows helper to run backend locally on port `8555`

## Prerequisites

- Python 3.10+
- Flutter SDK (stable)
- Appwrite project (for auth/data)

## Backend setup (local)

1. Create `.env` from `.env.example` and fill Appwrite values.
2. Create a virtual environment and install deps.
3. Run the API.

### Windows quick start

```powershell
./run.bat
```

This starts:
- `uvicorn skoolplannr.app:app --host 0.0.0.0 --port 8555 --reload`

### Manual start (cross-platform)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
set PYTHONPATH=src   # Windows PowerShell: $env:PYTHONPATH="src"
python -m uvicorn skoolplannr.app:app --host 0.0.0.0 --port 8555 --reload
```

## Flutter frontend

From `frontend/flutter`:

```bash
flutter pub get
flutter run -d chrome --web-port 5173
```

Default API base URL points to deployed backend. Override for local backend:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8555
```

Android emulator local backend:

```bash
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8555 --dart-define=ALLOW_LOCAL_API=true
```

## Appwrite Function backend

Function entrypoint:
- `appwrite/functions/backend/main.py`

Build command:

```bash
pip install -r appwrite/functions/backend/requirements.txt
```

The function exposes the same API routes used by Flutter (`/auth/login`, `/subjects`, `/tasks`, `/grades`, etc.).

## Environment variables

See `.env.example` for complete list. Key variables:

- `APPWRITE_ENDPOINT`
- `APPWRITE_PROJECT_ID`
- `APPWRITE_API_KEY` (or Appwrite function dynamic key fallback)
- `APPWRITE_DATABASE_ID`
- Collection IDs (`APPWRITE_*_COLLECTION_ID`)
- `CORS_ALLOWED_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX`

## API health check

```bash
GET /health
```

Expected response:

```json
{"status":"ok"}
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Notes

- Root files currently indicate an unresolved merge in some places (`requirements.txt`, `.env.example`) in this branch state. Resolve those before production packaging.
- `frontend/flutter/README.md` has client-specific run/deploy details.
- `appwrite/functions/backend/README.md` has function deployment specifics.
