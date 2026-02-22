# SkoolPlannr

SkoolPlannr now uses a **Python FastAPI backend** with a **Flutter frontend strategy**.

## Current Architecture
- Backend: FastAPI (`src/skoolplannr/app.py`)
- Data/Auth: Firebase Auth + Firestore
- Frontend: Flutter (`frontend/flutter`)

## Quick Start (Backend)
1. Install dependencies:
   - `python -m pip install --upgrade pip`
   - `python -m pip install -r requirements.txt`
2. Set `.env` values:
   - `FIREBASE_API_KEY`
   - `FIREBASE_PROJECT_ID`
   - `GOOGLE_APPLICATION_CREDENTIALS`
3. Run API:
   - `run.bat`
4. Verify:
   - `http://localhost:8555/health`
   - `http://localhost:8555/docs`

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
