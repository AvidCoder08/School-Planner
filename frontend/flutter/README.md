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

## Build Windows EXE + MSIX packages
Run this from `frontend/flutter`:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\package_windows.ps1
```

Optional API URL override:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\package_windows.ps1 -ApiUrl "http://localhost:8555"
```

Optional local test certificate password override:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\package_windows.ps1 -LocalCertPassword "YourStrongPassword123!"
```

This generates:
- `build\windows\packages\SchoolPlannr.exe`
- `build\windows\packages\*.dll` and `build\windows\packages\data\` (required runtime files for EXE)
- `build\windows\packages\SchoolPlannr-local-test.msix` (for local PC testing)
- `build\windows\packages\SchoolPlannr-store.msix` (Store submission workflow)

Important: Do not move `SchoolPlannr.exe` by itself. Keep it in `build\windows\packages` together with the copied DLLs and `data` folder, otherwise Windows will show missing `*_plugin.dll` errors.

For local testing, the script creates/reuses `tool\certs\schoolplannr-local-test.pfx`, trusts its `.cer` in your current user certificate store, and signs `SchoolPlannr-local-test.msix` with it.

If Windows still blocks install with certificate trust errors (`0x800B0109` / `0x800B010A`), run this once in **elevated PowerShell**:

```powershell
Import-Certificate -FilePath .\tool\certs\schoolplannr-local-test.cer -CertStoreLocation Cert:\LocalMachine\TrustedPeople
Import-Certificate -FilePath .\tool\certs\schoolplannr-local-test.cer -CertStoreLocation Cert:\LocalMachine\Root
```
