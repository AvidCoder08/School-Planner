# SkoolPlannr Deployment Guide (Detailed)

This guide walks through production deployment in the correct order:

1. Backend on **Appwrite Functions**
2. Flutter **Web** app
3. Flutter **Android** app

It is written for this repository and matches the code currently in place.

---

## 0) Architecture & what changed

### Current architecture
- Backend runtime: **Appwrite Function** (Python)
- Backend code root: `appwrite/functions/backend`
- Flutter frontend root: `frontend/flutter`
- Data/Auth provider: **Appwrite**

### Important backend behavior
- The function exposes the same routes your Flutter app already calls (`/auth/login`, `/subjects`, `/tasks`, etc.)
- You do **not** need your PC backend running in production
- `APPWRITE_API_KEY` is optional for function runtime because code falls back to `APPWRITE_FUNCTION_API_KEY`

---

## 1) Prerequisites checklist

## 1.1 Accounts
- Appwrite Cloud project access
- Firebase project access (if using Firebase Hosting for web)
- Google Play Console access (for Android publishing)

## 1.2 Tools on your machine
- Flutter SDK (stable)
- Git
- Python 3.x (for local checks)
- Node.js + npm (for Firebase CLI if using Firebase Hosting)

## 1.3 Project IDs and values (for this repo)
- Appwrite endpoint: `https://sgp.cloud.appwrite.io/v1`
- Appwrite project id: `699c792c002591020870`
- Appwrite database id: your database id (example from your docs: `imosm867`)

---

## 2) Backend deployment to Appwrite Functions

## 2.1 Function code location
Use this folder as Function root:

- repository root (this project root)

Entrypoint:

- `appwrite/functions/backend/main.py`

Build command:

- `pip install -r appwrite/functions/backend/requirements.txt`

Runtime:

- Python (latest stable available in Appwrite Console)

## 2.2 Create function in Appwrite Console
1. Open Appwrite Console → **Functions**.
2. Click **Create function**.
3. Name it: `school-planner-backend` (or similar).
4. Choose Python runtime.
5. Configure source/deploy from Git (recommended), or upload manually.
6. Set root directory to repository root.
7. Set entrypoint to `appwrite/functions/backend/main.py`.
8. Set build command to `pip install -r appwrite/functions/backend/requirements.txt`.

## 2.3 Environment variables for function
Add these in Function Settings → Environment Variables:

```env
APPWRITE_ENDPOINT=https://sgp.cloud.appwrite.io/v1
APPWRITE_PROJECT_ID=699c792c002591020870
APPWRITE_DATABASE_ID=<YOUR_DATABASE_ID>

APPWRITE_USERS_COLLECTION_ID=users
APPWRITE_YEARS_COLLECTION_ID=academic_years
APPWRITE_TERMS_COLLECTION_ID=terms
APPWRITE_SUBJECTS_COLLECTION_ID=subjects
APPWRITE_TASKS_COLLECTION_ID=tasks
APPWRITE_EVENTS_COLLECTION_ID=events
APPWRITE_GRADES_COLLECTION_ID=grades
APPWRITE_ASSESSMENTS_COLLECTION_ID=assessments

CORS_ALLOWED_ORIGINS=https://<your-web-domain>,http://localhost:5173,http://127.0.0.1:5173
CORS_ALLOW_ORIGIN_REGEX=^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$
```

Notes:
- `APPWRITE_API_KEY` is optional in Functions runtime.
- Dynamic key fallback is supported in code.
- Use `APPWRITE_FUNCTION_DEBUG=true` only temporarily for debugging.

## 2.4 Function execute access and domain
1. In function settings, configure **Execute access**.
2. If you will call via function domain from app/web, set execute access so requests can run (commonly `Any`).
3. Open **Domains** tab and copy generated function domain.
   - Example shape: `https://xxxxxxxx.appwrite.global`

This domain becomes your new API base URL.

## 2.5 Required function scopes/permissions
Grant scopes required by your backend operations:
- Databases read/write
- Documents read/write
- Account/session operations used by auth routes

If any endpoint fails with permission errors, review function scopes first.

## 2.6 Backend verification (post-deploy)
Use function domain for all tests:

```bash
curl https://<function-domain>/health
```

Expected:

```json
{"status":"ok"}
```

Then test key routes from Postman/Insomnia/curl:
- `POST /auth/signup`
- `POST /auth/login`
- `GET /profile` with `x-user-id`
- `GET /subjects` with `x-user-id`

If CORS fails on web, confirm `CORS_ALLOWED_ORIGINS` includes your exact frontend URL.

---

## 3) Web app deployment (Flutter Web)

## 3.1 Build web with production API URL
From `frontend/flutter`:

```bash
flutter clean
flutter pub get
flutter build web --release --dart-define=API_BASE_URL=https://<function-domain>
```

This compile-time define is mandatory for production.

## 3.2 Option A: Appwrite Sites (recommended)
Use Appwrite Sites to host the Flutter web build.

In Appwrite Console:
1. Go to **Sites** → **Create site**.
2. Choose static site deployment (Git or manual upload).
3. If using Git, set:
  - Root directory: `frontend/flutter`
  - Build command: `flutter build web --release --dart-define=API_BASE_URL=https://<function-domain>`
  - Output directory: `build/web`
4. If using manual upload, first build locally and upload `frontend/flutter/build/web`.
5. Open the generated site domain and verify the app loads.

## 3.3 Option B: Any static host
Upload contents of `frontend/flutter/build/web` to your host (Cloudflare Pages, Netlify, Vercel static, S3, etc.).

## 3.4 Web verification
- Open production web URL
- Sign up/login
- Perform CRUD: subjects/tasks/events
- Save/list grades
- Check browser network tab:
  - requests hit `https://<function-domain>/...`
  - no CORS errors

---

## 4) Android deployment (APK release)

## 4.1 Keystore and signing
Your repo is already wired to use `frontend/flutter/android/key.properties`.

Required values in `key.properties`:

```properties
storePassword=<real_store_password>
keyPassword=<real_key_password>
keyAlias=upload
storeFile=C:\\Users\\soham\\upload-keystore.jks
```

Ensure keystore file exists at `storeFile` path.

## 4.2 Android app id
Current app id configured:

- `com.notacoder.schoolplannr`

Keep this stable after publishing.

## 4.3 Build release APK
From `frontend/flutter`:

```bash
flutter clean
flutter pub get
flutter build apk --release --dart-define=API_BASE_URL=https://<function-domain>
```

Output:

- `build/app/outputs/flutter-apk/app-release.apk`

## 4.4 APK distribution/testing
1. Build `app-release.apk`.
2. Share APK with testers (direct file share or Play Console **Internal app sharing**).
3. Install on test devices and validate login, CRUD, attendance, grades.
4. For production Play Store release, build an AAB separately.

---

## 5) Appwrite platform registration

Because your Flutter app also uses Appwrite SDK in client code, register platforms in Appwrite Project settings:

- Web platform with your deployed web domain
- Android platform with package name `com.notacoder.schoolplannr`
- Add required Android SHA fingerprints as needed

---

## 6) Cutover strategy (safe rollout)

## 6.1 Staging first
1. Deploy function.
2. Build web with function domain.
3. Validate end-to-end using test account.
4. Only then deploy production web + Android internal testing.

## 6.2 Rollback plan
Keep previous known-good app build and config.
If function deployment causes regressions:
1. Repoint frontend to previous backend base URL.
2. Redeploy web.
3. Pause Android rollout.

---

## 7) Common failures and fixes

## 7.1 401 Missing x-user-id
Cause: frontend request missing session header.
Fix: ensure user is logged in and `ApiClient` sends `x-user-id` for non-auth routes.

## 7.2 CORS blocked on web
Cause: web domain not listed in `CORS_ALLOWED_ORIGINS`.
Fix: add exact origin and redeploy function.

## 7.3 Function returns INTERNAL_SERVER_ERROR
Cause: unhandled exception.
Fix:
1. Set `APPWRITE_FUNCTION_DEBUG=true` temporarily.
2. Re-run request.
3. Inspect logs in Function Executions.
4. Disable debug flag after fixing.

## 7.4 Android cannot reach API
Cause: wrong `API_BASE_URL` define or backend unavailable.
Fix: rebuild with correct function domain and verify `/health` endpoint.

## 7.5 Appwrite permission denied
Cause: missing function scopes.
Fix: expand function scopes for required database/document/account operations.

---

## 8) Exact command recap

## 8.1 Web release
```bash
cd frontend/flutter
flutter clean
flutter pub get
flutter build web --release --dart-define=API_BASE_URL=https://<function-domain>
firebase deploy --only hosting
```

## 8.2 Android release
```bash
cd frontend/flutter
flutter clean
flutter pub get
flutter build apk --release --dart-define=API_BASE_URL=https://<function-domain>
```

---

## 9) Final production checklist

- [ ] Function deployed successfully
- [ ] `/health` returns ok on function domain
- [ ] CORS includes production web origin
- [ ] Web deployed with correct `API_BASE_URL`
- [ ] Android APK built with correct `API_BASE_URL`
- [ ] Internal Android test pass completed
- [ ] Appwrite platforms (web/android) configured
- [ ] No secrets committed to git

---

## 10) File map (for this migration)

- Function backend entrypoint: `appwrite/functions/backend/main.py`
- Function dependencies: `appwrite/functions/backend/requirements.txt`
- Function setup doc: `appwrite/functions/backend/README.md`
- Backend settings: `src/skoolplannr/config/settings.py`
- Existing API (legacy local run): `src/skoolplannr/app.py`
- Flutter app API base URL logic: `frontend/flutter/lib/main.dart`
- Android signing config: `frontend/flutter/android/app/build.gradle.kts`
- Android signing secrets file: `frontend/flutter/android/key.properties`

If you want, the next step is I can also generate a **deployment checklist template** (staging/prod sign-off sheet) you can reuse each release.