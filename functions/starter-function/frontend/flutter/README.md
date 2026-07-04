# SkoolPlannr Flutter Frontend

This is the active frontend for SkoolPlannr.

## Requirements
- Flutter SDK (stable)

## Run (Web)
```bash
flutter pub get
flutter run -d chrome --web-port 5173
```

## API Base URL
The app uses the deployed backend by default:
`https://699cb5430037a8a18f1c.sgp.appwrite.run`

To override, pass a Dart define:
```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8555
```

For local backend testing on Android emulator, use both defines:
```bash
flutter run -d emulator-5554 \
  --dart-define=API_BASE_URL=http://10.0.2.2:8555 \
  --dart-define=ALLOW_LOCAL_API=true
```

## Build Android APK (PowerShell)
Run this from `frontend/flutter`:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\build_android_apk.ps1
```

Override function domain / API base URL:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\build_android_apk.ps1 -FunctionDomain "https://your-function-domain.appwrite.run"
```

If you need local emulator backend in release build:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\build_android_apk.ps1 -FunctionDomain "http://10.0.2.2:8555" -AllowLocalApi
```

Note: Local loopback URLs (10.0.2.2, localhost, 127.0.0.1) are blocked by default in release builds for security.

## F-Droid / Open-source Android release

This project is configured so Android release builds do not require a private
keystore in CI/F-Droid builds.

Build unsigned release APK locally:

```bash
flutter build apk --release
```

Build unsigned release App Bundle locally:

```bash
flutter build appbundle --release
```

Local manual signing (optional):
- Copy `android/key.properties.example` to `android/key.properties`.
- Fill in your local keystore values.
- Keep `android/key.properties` untracked.

F-Droid metadata for store listing text is available at:
- `fastlane/metadata/android/en-US/`

## Build/Deploy Web (PowerShell)
Run this from `frontend/flutter`:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1
```

By default, this script builds the web app and deploys it to your **linked Vercel app** (production) using `vercel deploy --prod`.
Before first use, link this folder once:

```powershell
vercel link
```

Optional API URL override:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1 -ApiUrl "https://your-function-domain.appwrite.run"
```

Optional base href (for sub-path hosting such as `/schoolplannr/`):

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1 -BaseHref "/schoolplannr/"
```

Optional deploy target directory (copies `build\web\*` there after build):

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1 -DeployDir "C:\inetpub\wwwroot\schoolplannr"
```

Optional Vercel controls:

```powershell
# Build artifacts only (skip Vercel deploy)
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1 -DeployToVercel:$false

# Preview deployment instead of production
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1 -VercelProd:$false

# CI usage with token/scope
powershell -ExecutionPolicy Bypass -File .\tool\deploy_web.ps1 -VercelToken "<token>" -VercelScope "<team-or-user>"
```

This generates:
- `build\web\` (Flutter web output)
- `build\web_artifacts\site\` (staged deploy folder)
- `build\web_artifacts\schoolplannr-web-<timestamp>.zip` (uploadable artifact)

The script also writes a `vercel.json` in the staged output to ensure Flutter SPA deep links route to `index.html` on Vercel.
