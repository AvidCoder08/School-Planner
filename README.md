# SkoolPlannr

Multi-platform student planner and grade tracker built with **Python + Flet** and **Firebase**.

## 1) Firebase Setup Instructions

### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/).
2. Click **Create a project**.
3. Name it `SkoolPlannr` (or your preferred name).
4. Disable Google Analytics (optional for MVP).
5. Create project.

### Step 2: Add Apps (Web + Android + iOS)
Even though Flet runs Python, registering platform apps helps with Firebase services:
1. In project settings, add:
	 - **Web app** (for Flet web builds)
	 - **Android app** (package id for mobile build)
	 - **iOS app** (bundle id for iOS build)
2. Save generated config values (API key, project id, etc.).

#### Android app registration details (Firebase Project Settings)
When you click **Add app → Android**, fill these fields:

1. **Android package name (required)**
	- Must exactly match your Android app id.
	- Recommended reverse-domain format: `com.<yourname>.skoolplannr`.
	- This value cannot be changed later in Firebase.

2. **App nickname (optional but recommended)**
	- Example: `SkoolPlannr Android`.

3. **Debug signing certificate SHA-1 (optional now, needed for Google Sign-In/Phone Auth/App Check)**
	- You can skip for email/password-only MVP.
	- Add SHA-1 now if you plan to use Google Sign-In later.

4. Click **Register app**.

5. Download **google-services.json** and keep it secure.
	- If you move to native Firebase SDK integration later, this file must be added to the Android app module.

6. In **Project settings → Your apps → Android app**, verify:
	- Package name is correct.
	- SHA certificate fingerprints are added (when needed).
	- App status is active.

#### iOS app registration details (Firebase Project Settings)
When you click **Add app → iOS**, fill these fields:

1. **iOS bundle ID (required)**
	- Must exactly match Xcode bundle id.
	- Recommended format: `com.<yourname>.skoolplannr`.
	- Cannot be changed later in Firebase.

2. **App nickname (optional but recommended)**
	- Example: `SkoolPlannr iOS`.

3. **App Store ID (optional)**
	- Leave empty until the app is published.

4. Click **Register app**.

5. Download **GoogleService-Info.plist** and keep it secure.
	- If you move to native Firebase SDK integration later, this file must be included in the iOS Runner target.

6. In **Project settings → Your apps → iOS app**, verify:
	- Bundle ID is correct.
	- API key and App ID are generated.
	- App status is active.

#### Notes specific to current SkoolPlannr scaffold
- Current Module 1 uses Firebase Auth REST API (`FIREBASE_API_KEY`) and Firestore via Admin SDK (`GOOGLE_APPLICATION_CREDENTIALS`).
- `google-services.json` and `GoogleService-Info.plist` are not required for the current Python-only auth/onboarding flow.
- Keep both app registrations done now so future Android/iOS native Firebase features can be enabled without rework.

### Step 3: Enable Authentication (Email/Password)
1. Open **Build → Authentication → Get started**.
2. In **Sign-in method**, enable **Email/Password**.
3. Optionally enable email verification requirement.

#### Password policy configured for SkoolPlannr
In **Authentication → Settings → Password policy**, use:
- **Enforcement mode**: `Require enforcement`
- **Minimum password length**: `8`
- **Maximum password length**: `4096` (default)
- **Require uppercase character**: enabled
- **Require lowercase character**: enabled
- **Require numeric character**: enabled
- **Require special character**: enabled
- **Force upgrade on sign-in**: disabled (for now)

This means weak/non-compliant passwords are blocked at sign-up by Firebase before account creation.

### Step 4: Create Firestore Database
1. Open **Build → Firestore Database**.
2. Click **Create database**.
3. Start in **Production mode**.
4. Choose nearest region.

### Step 5: Firestore Security Rules (User Isolation)
Use rules that let users read/write only their own data:

```firestore
rules_version = '2';
service cloud.firestore {
	match /databases/{database}/documents {

		function isSignedIn() {
			return request.auth != null;
		}

		function isOwner(uid) {
			return isSignedIn() && request.auth.uid == uid;
		}

		// Root user document
		match /users/{uid} {
			allow read, write: if isOwner(uid);

			// Any subcollection under that user is private to same uid
			match /{document=**} {
				allow read, write: if isOwner(uid);
			}
		}

		// deny everything else by default
		match /{document=**} {
			allow read, write: if false;
		}
	}
}
```

### Step 6: Service Account (Backend/Admin Scripts)
1. Go to **Project settings → Service accounts**.
2. Generate private key JSON.
3. Store it securely (never commit to git).
4. Use env var like `GOOGLE_APPLICATION_CREDENTIALS` or load from secure path.

---

## 2) Firestore Database Schema Design

Use **user-scoped hierarchical schema**:

```text
users/{uid}
	profile (doc fields)
	academic_years/{year_id}
		terms/{term_id}
			subjects/{subject_id}
				assessments/{assessment_id}
			tasks/{task_id}
			events/{event_id}
			grades/{subject_id}
```

### Collections & Fields

#### `users/{uid}`
- `email`: string
- `display_name`: string
- `created_at`: timestamp
- `active_year_id`: string
- `active_term_id`: string

#### `users/{uid}/academic_years/{year_id}`
- `label`: string (e.g., `2025-2026`)
- `start_date`: timestamp
- `end_date`: timestamp

#### `users/{uid}/academic_years/{year_id}/terms/{term_id}`
- `name`: string (e.g., `Fall Semester`)
- `start_date`: timestamp
- `end_date`: timestamp
- `status`: string (`active`, `completed`, `upcoming`)
- `sgpa`: number (derived, optional cached)

#### `.../subjects/{subject_id}`
- `name`: string
- `instructor`: string
- `location`: string
- `credits`: number (`2`, `4`, `5`)
- `schedule_slots`: array of objects
	- `day`: string (`Mon`...`Sun`)
	- `start_time`: string (`HH:MM`)
	- `end_time`: string (`HH:MM`)

#### `.../subjects/{subject_id}/assessments/{assessment_id}`
- `type`: string (`ISA1`, `ISA2`, `ESA`, `A1`, `A2`, `A3`, `A4`, `LAB`)
- `max_raw`: number
- `weight_to`: number
- `score_raw`: number
- `score_weighted`: number (derived)

#### `.../tasks/{task_id}`
- `title`: string
- `description`: string
- `subject_id`: string (nullable)
- `task_type`: string (`assignment`, `homework`, `project`, `exam`)
- `due_at`: timestamp
- `completed`: boolean
- `priority`: string (`low`, `medium`, `high`)
- `created_at`: timestamp

#### `.../events/{event_id}`
- `title`: string
- `event_type`: string (`class`, `exam`, `holiday`, `deadline`)
- `starts_at`: timestamp
- `ends_at`: timestamp
- `subject_id`: string (nullable)

#### `.../grades/{subject_id}` (summary cache)
- `final_score_100`: number
- `letter_grade`: string
- `grade_point`: number
- `updated_at`: timestamp

### Index Recommendations
- `tasks`: composite index on `(completed ASC, due_at ASC)`.
- `events`: index on `(starts_at ASC)`.
- `subjects`: single-field index on `credits`.

---

## 3) Recommended Project Structure (Python + Flet)

```text
School-Planner/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ src/
│  └─ skoolplannr/
│     ├─ app.py
│     ├─ config/
│     │  ├─ settings.py
│     │  └─ firebase_config.py
│     ├─ core/
│     │  ├─ grades.py
│     │  ├─ gpa.py
│     │  └─ models.py
│     ├─ services/
│     │  ├─ auth_service.py
│     │  ├─ firestore_service.py
│     │  ├─ schedule_service.py
│     │  └─ task_service.py
│     ├─ state/
│     │  ├─ app_state.py
│     │  └─ session_state.py
│     ├─ ui/
│     │  ├─ views/
│     │  │  ├─ login_view.py
│     │  │  ├─ onboarding_view.py
│     │  │  ├─ dashboard_view.py
│     │  │  ├─ subjects_view.py
│     │  │  ├─ tasks_view.py
│     │  │  └─ grades_view.py
│     │  └─ components/
│     │     ├─ timetable_card.py
│     │     ├─ task_tile.py
│     │     └─ grade_chart.py
│     └─ utils/
│        ├─ datetime_utils.py
│        └─ validators.py
└─ tests/
	 ├─ test_grades.py
	 └─ test_gpa.py
```

---

## 4) Core Logic Implementation (Code)

Production-ready implementation is provided in:
- `src/skoolplannr/core/grades.py`
- `src/skoolplannr/core/gpa.py`

### Grade Conversion Table

| Letter Grade | Marks Range | Grade Point |
|---|---|---|
| S | 90 - 100 | 10 |
| A | 80 - 89 | 9 |
| B | 70 - 79 | 8 |
| C | 60 - 69 | 7 |
| D | 50 - 59 | 6 |
| E | 40 - 49 | 5 |
| F | 0 - 39 | 4 |

---

## 5) Phased Development Plan

### Phase 1 — Foundation
1. Initialize Flet app shell and route system.
2. Add config loader (`.env`) and Firebase client setup.
3. Implement Email/Password auth (sign up, login, logout).
4. Build onboarding flow (academic year + terms).

### Phase 2 — Core Data Modules
1. Subjects CRUD.
2. Timetable entry for each subject.
3. Tasks CRUD with due date/time and completion state.
4. Basic dashboard showing date/time, today classes, due tasks.

### Phase 3 — Smart Dashboard + Calendar
1. “Today” auto-switch to next day schedule when classes end.
2. Unified calendar/events (classes, exams, deadlines, holidays).
3. Tomorrow/Today task prioritization cards.

### Phase 4 — Grade System
1. Assessment input UI per credit model.
2. Integrate weighted score engine.
3. Final score to letter grade + grade point conversion.
4. SGPA + CGPA calculations and persistence.

### Phase 5 — Analytics + Quality
1. SGPA/CGPA trend graphs.
2. Unit tests for grade and GPA logic.
3. Offline-first caching and sync conflict handling.
4. Packaging for Windows/Web/Android/iOS.

---

## 6) Recommendations (Tools, Libraries, Concepts)

- **Flet state management**: keep a centralized `AppState` object and use controlled updates in views.
- **Data validation (optional)**: `pydantic` models for request/response validation (recommended when using Python versions with compatible wheels).
- **Date handling**: `python-dateutil` and timezone-safe UTC storage.
- **Charts**: use Flet chart controls (or matplotlib-generated images if needed).
- **Offline support**: local persistence via `sqlite`/`tinydb` cache + background sync queue.
- **Background reminders**: platform-specific notifications for mobile, local notifications for desktop.
- **Dependency management**: pinned `requirements.txt`, optional `pip-tools` for lock workflow.
- **Secrets management**: `.env` + `.gitignore` + separate Firebase service account path.
- **Testing**: `pytest` for unit tests (especially grade/GPA logic).

---

## Quick Start (Developer)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
flet run src/skoolplannr/app.py
```

If you run without Flet CLI, use:

```bash
set PYTHONPATH=src
python src/skoolplannr/app.py
```

Windows quick start: double-click `run.bat` from project root.

### Module 1 Environment Notes
- Set `FIREBASE_API_KEY` in `.env` for email/password auth REST calls.
- Set `FIREBASE_PROJECT_ID` in `.env`.
- Set `GOOGLE_APPLICATION_CREDENTIALS` to your Firebase service account JSON path (needed for Firestore write/read in current scaffold).

### Module 2 (Current Implementation) — How to Use
1. Login and finish onboarding.
2. Open **Dashboard** and click **Manage Subjects**.
3. Add subjects with schedule format like: `Mon 10:00-11:00, Wed 14:00-15:00`.
4. Return to dashboard and verify timetable appears for today.
5. If all classes for today are over, dashboard automatically shows next scheduled day.
6. Click **Manage Tasks** and add tasks using due format: `YYYY-MM-DD HH:MM`.
7. Dashboard shows incomplete tasks due **today or tomorrow**.

### Module 3 (Current Implementation) — Calendar & Events
1. From the dashboard, click **Open Calendar**.
2. Add events with start/end format: `YYYY-MM-DD HH:MM`.
3. Choose an event type (`class`, `exam`, `holiday`, `deadline`).
4. Link to a subject if relevant, or leave blank.
5. Dashboard shows the next 3 upcoming events.

### Module 4 & 5 (Current Implementation) — Grades, SGPA, CGPA
1. From the dashboard, click **Grades**.
2. Select a subject and enter scores for all required assessments.
3. Click **Calculate & Save** to store assessments and grade summary.
4. SGPA for the current term updates after at least one grade is saved.
5. CGPA is computed from all terms that have stored SGPA values.
6. The **SGPA Trend** bar list provides a visual overview across semesters.

---

## MVP Checklist (Aligned to Your User Stories)

- [ ] Email/password signup + signin
- [ ] Post-signup onboarding (year, terms, dates)
- [ ] Dashboard with current time/date + today/next schedule
- [ ] Subject CRUD with instructor/location/credits/timings
- [ ] Task CRUD with due date/time + completion
- [ ] Calendar for exams/assignments/holidays
- [ ] Grade input (2/4/5 credits)
- [ ] Letter grade + grade point conversion
- [ ] SGPA + CGPA calculation
- [ ] SGPA/CGPA trend graph


