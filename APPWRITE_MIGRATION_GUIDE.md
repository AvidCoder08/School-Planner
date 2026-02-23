# Firebase to Appwrite Migration Guide (Detailed)

This guide is tailored to this repository (`School-Planner`) and reflects the migration already applied in code. Use it as the operational checklist to get a stable Appwrite-backed setup in development and production.

---

## 1) Migration outcome (what is already changed in code)

### Backend
- Auth moved from Firebase Identity Toolkit to Appwrite Account APIs:
  - `src/skoolplannr/services/auth_service.py`
- Data layer moved from Firestore to Appwrite Databases:
  - `src/skoolplannr/services/appwrite_service.py`
- API endpoints rewired to use Appwrite services:
  - `src/skoolplannr/app.py`
- Settings now read `APPWRITE_*` env vars:
  - `src/skoolplannr/config/settings.py`
- Dependencies and run script updated:
  - `requirements.txt`
  - `run.bat`

### Flutter
- Appwrite SDK added to Flutter app:
  - `frontend/flutter/pubspec.yaml`
- Global Appwrite client configured with project values:
  - `frontend/flutter/lib/services/appwrite_client.dart`
- Dashboard button to trigger ping:
  - `frontend/flutter/lib/pages/dashboard_page.dart`
- Environment constants file:
  - `frontend/flutter/lib/config/environment.dart`
- Sign-up now captures `name` and sends it to backend signup API:
  - `frontend/flutter/lib/pages/auth_page.dart`
  - `frontend/flutter/lib/main.dart`
- PESU credentials are managed in Settings and consumed by Attendance:
  - `frontend/flutter/lib/pages/settings_page.dart`
  - `frontend/flutter/lib/pages/attendance_page.dart`
- Agenda/Calendar event type includes `holiday` option:
  - `frontend/flutter/lib/pages/add_event_page.dart`
  - `frontend/flutter/lib/pages/calendar_page.dart`

---

## 2) Appwrite project values used in this repository

```dart
class Environment {
  static const String appwriteProjectId = '699c792c002591020870';
  static const String appwriteProjectName = 'schoolplannr';
  static const String appwritePublicEndpoint = 'https://sgp.cloud.appwrite.io/v1';
}
```

Use these values consistently in Appwrite Console and in app code.

---

## 3) Prerequisites

- Appwrite Cloud project (`schoolplannr`) exists.
- You can create:
  - API key
  - Database
  - Collections + attributes + indexes
- Python environment works via `run.bat`.
- Flutter SDK installed and `flutter doctor` is healthy.

---

## 4) Appwrite Console setup (required)

## 4.1 Create API key
Create a **server API key** with read/write permissions for your database/documents.

Minimum practical permissions:
- Databases: read/write
- Documents: read/write
- Users: read (optional but useful)

Save this key securely. It goes into backend `.env` as `APPWRITE_API_KEY`.

## 4.2 Create database
Create one Appwrite Database and note the `databaseId`. -> imosm867

## 4.3 Create collections
Create these 8 collections (or set custom names via env):

1. `users`
2. `academic_years`
3. `terms`
4. `subjects`
5. `tasks`
6. `events`
7. `grades`
8. `assessments`

If names differ, map them using the `APPWRITE_*_COLLECTION_ID` env vars in section 6.

---

## 5) Schema contract (exact attributes expected by backend)

Create attributes as follows (required/optional as indicated).

## 5.1 `users`
- `uid` (string, required)
- `email` (string/email, required)
- `created_at` (string datetime, required)
- `active_year_id` (string, optional)
- `active_term_id` (string, optional)
- `cgpa` (double, optional)

## 5.2 `academic_years`
- `user_id` (string, required)
- `label` (string, required)
- `start_date` (string datetime, required)
- `end_date` (string datetime, required)
- `created_at` (string datetime, required)

## 5.3 `terms`
- `user_id` (string, required)
- `year_id` (string, required)
- `name` (string, required)
- `start_date` (string datetime, required)
- `end_date` (string datetime, required)
- `status` (string, required)
- `sgpa` (double, optional)
- `total_credits` (integer, optional)

## 5.4 `subjects`
- `user_id` (string, required)
- `year_id` (string, required)
- `term_id` (string, required)
- `name` (string, required)
- `instructor` (string, optional)
- `location` (string, optional)
- `credits` (integer, required)
- `schedule_slots` (string, optional)
- `created_at` (string datetime, required)

Note: `schedule_slots` is stored as a JSON string by backend code.

## 5.5 `tasks`
- `user_id` (string, required)
- `year_id` (string, required)
- `term_id` (string, required)
- `title` (string, required)
- `description` (string, optional)
- `subject_id` (string, optional)
- `task_type` (string, required)
- `due_at` (string datetime, required)
- `completed` (boolean, required)
- `priority` (string, required)
- `created_at` (string datetime, required)

## 5.6 `events`
- `user_id` (string, required)
- `year_id` (string, required)
- `term_id` (string, required)
- `title` (string, required)
- `event_type` (string, required)
- `starts_at` (string datetime, required)
- `ends_at` (string datetime, required)
- `subject_id` (string, optional)
- `created_at` (string datetime, required)

Common `event_type` values used in the app UI:
- `class`
- `exam`
- `assignment`
- `attendance`
- `holiday`

## 5.7 `grades`
- `user_id` (string, required)
- `subject_id` (string, required)
- `subject_name` (string, required)
- `credits` (integer, required)
- `final_score_100` (double, required)
- `letter_grade` (string, required)
- `grade_point` (integer, required)
- `updated_at` (string datetime, required)
- `partial` (boolean, required)

## 5.8 `assessments`
- `user_id` (string, required)
- `subject_id` (string, required)
- `type` (string, required)
- `max_raw` (double, required)
- `weight_to` (double, required)
- `score_raw` (double, required)
- `score_weighted` (double, required)

---

## 6) Backend environment setup

Update root `.env`:

```dotenv
APPWRITE_ENDPOINT=https://sgp.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=699c792c002591020870
APPWRITE_API_KEY=<YOUR_SERVER_API_KEY>
APPWRITE_DATABASE_ID=<YOUR_DATABASE_ID>

APPWRITE_USERS_COLLECTION_ID=users
APPWRITE_YEARS_COLLECTION_ID=academic_years
APPWRITE_TERMS_COLLECTION_ID=terms
APPWRITE_SUBJECTS_COLLECTION_ID=subjects
APPWRITE_TASKS_COLLECTION_ID=tasks
APPWRITE_EVENTS_COLLECTION_ID=events
APPWRITE_GRADES_COLLECTION_ID=grades
APPWRITE_ASSESSMENTS_COLLECTION_ID=assessments
```

Then run backend:

```bat
run.bat
```

Health checks:
- `http://localhost:8555/health`
- `http://localhost:8555/docs`

Signup/login payload contract used by backend:

```json
// POST /auth/signup
{
  "email": "student@example.com",
  "password": "<password>",
  "name": "Student Name"
}

// POST /auth/login
{
  "email": "student@example.com",
  "password": "<password>"
}
```

`name` is optional in backend schema and is only sent from the Flutter app during signup.

---

## 7) Flutter Appwrite setup

Already applied in this repository, but listed here for reproducibility.

## 7.1 Install SDK
```bash
flutter pub add appwrite:21.1.0
```

## 7.2 Create global client
`frontend/flutter/lib/services/appwrite_client.dart`

```dart
import 'package:appwrite/appwrite.dart';

final Client client = Client()
  .setProject('699c792c002591020870')
  .setEndpoint('https://sgp.cloud.appwrite.io/v1');
```

## 7.3 Add ping action on homepage
The dashboard includes a **Send a ping** button that calls:

```dart
await client.ping();
```

---

## 8) Verification checklist (end-to-end)

1. Start backend with `run.bat`.
2. Start Flutter on Edge:
   ```bash
   flutter run -d edge
   ```
3. In app:
  - Sign up (enter **name**, email, password) / login
   - Complete onboarding
   - Create/list/delete subject
   - Create/list/toggle/delete task
  - Create/list/delete event (including `holiday` type)
   - Save/list grade
  - Open Settings and save PESU credentials
  - Open Attendance and fetch attendance using saved credentials
4. On dashboard click **Send a ping**.
5. Confirm no exceptions in terminal/browser console.

---

## 9) Data migration options from Firebase

## Option A: clean start (recommended if acceptable)
- Do not import historical Firebase data.
- New users and records are created in Appwrite naturally.

## Option B: historical import
If you need old data:
1. Export Firestore data.
2. Transform nested Firestore structure to flat Appwrite collections.
3. Preserve IDs used by references (`uid`, `year_id`, `term_id`, `subject_id`).
4. Convert timestamps to ISO-8601 strings.
5. JSON-encode `schedule_slots`.
6. Import in this order:
   - `users`
   - `academic_years`
   - `terms`
   - `subjects`
   - `tasks`, `events`
   - `assessments`
   - `grades`
7. Validate `users.active_year_id` and `users.active_term_id` after import.

---

## 10) TLS/certificate handshake errors (common on local machines)

If you see:
- `HandshakeException`
- `CERTIFICATE_VERIFY_FAILED`

This is usually local trust-store/proxy/antivirus interception, not Appwrite credentials.

## Temporary dev workaround
In Appwrite client you can set:

```dart
.setSelfSigned(status: true)
```

Use this only for development.

## Proper fix
- Update Windows root certificates.
- Check HTTPS interception by antivirus/proxy.
- If corporate network is used, trust the corporate root CA in system store.

---

## 11) Rollback plan (if needed)

If you must revert quickly:
1. Restore Firebase service files and imports.
2. Revert env vars from `APPWRITE_*` back to `FIREBASE_*`.
3. Revert dependencies and run script checks.
4. Restart backend and re-test auth + CRUD.

Use `git revert` or checkout prior commit safely.

---

## 12) Optional cleanup after stabilization

When Appwrite is confirmed stable, remove Firebase leftovers only if unused:
- `api.json`
- `google-services.json`
- `GoogleService-Info.plist`

Keep them if any deployment path still relies on Firebase.

---

## 13) Fast troubleshooting map

- **401/403 from backend calls**: API key scope issue or wrong endpoint/project.
- **Document creation fails**: missing attribute in collection schema.
- **Query errors**: missing indexes for filtered fields.
- **Auth success, profile empty**: `users` collection write/read mismatch.
- **Attendance asks for PESU credentials**: save credentials in Settings first.
- **Ping fails with TLS error**: local certificate chain issue.

---

## 14) File reference map

- Backend API entry: `src/skoolplannr/app.py`
- Appwrite auth adapter: `src/skoolplannr/services/auth_service.py`
- Appwrite data adapter: `src/skoolplannr/services/appwrite_service.py`
- Env loader: `src/skoolplannr/config/settings.py`
- Backend runner: `run.bat`
- Flutter Appwrite client: `frontend/flutter/lib/services/appwrite_client.dart`
- Flutter environment constants: `frontend/flutter/lib/config/environment.dart`
- Ping button UI: `frontend/flutter/lib/pages/dashboard_page.dart`
- Auth UI (signup name field): `frontend/flutter/lib/pages/auth_page.dart`
- Settings PESU credential manager: `frontend/flutter/lib/pages/settings_page.dart`
- Attendance view (uses saved credentials): `frontend/flutter/lib/pages/attendance_page.dart`
- Agenda/Calendar holiday option: `frontend/flutter/lib/pages/add_event_page.dart`, `frontend/flutter/lib/pages/calendar_page.dart`

This completes the detailed migration runbook for this repository.
