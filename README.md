# SkoolPlannr

SkoolPlannr now uses a **Python FastAPI backend** with a **Flutter frontend strategy**.

## Current Architecture
- Backend: FastAPI (`src/skoolplannr/app.py`)
- Data/Auth: Appwrite Auth + Appwrite Databases
- Frontend: Flutter (`frontend/flutter`)

## Quick Start (Backend)
1. Install dependencies:
   - `python -m pip install --upgrade pip`
   - `python -m pip install -r requirements.txt`
2. Set `.env` values:
   - `APPWRITE_ENDPOINT` (for example `https://<REGION>.cloud.appwrite.io/v1`)
   - `APPWRITE_PROJECT_ID`
   - `APPWRITE_API_KEY`
   - `APPWRITE_DATABASE_ID`
   - Optional: `APPWRITE_*_COLLECTION_ID` overrides (see `.env.example`)
3. Run API:
   - `run.bat`
4. Verify:
   - `http://localhost:8555/health`
   - `http://localhost:8555/docs`

## Production Backend (Appwrite Functions)
- Function backend code is available at `appwrite/functions/backend`.
- Deploy this folder as a Python Appwrite Function (entrypoint `main.py`, build command `pip install -r requirements.txt`).
- Full setup instructions: `appwrite/functions/backend/README.md`.

## Migration Guide
- Detailed Firebase -> Appwrite migration steps are in `APPWRITE_MIGRATION_GUIDE.md`.

## Quick Start (Flutter Frontend)
1. Install Flutter SDK (stable channel)
2. Open `frontend/flutter`
3. Run:
   - `flutter pub get`
   - `flutter run -d chrome --web-port 5173`
4. Optional API override:
   - `flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8555`

## Frontend Notes
- Legacy React frontend files have been removed.
- Active frontend is Flutter in `frontend/flutter`.
- Attendance page supports PESU Academy fetch via backend (`/attendance/pesu`) and securely persists PESU credentials per signed-in user on device.
