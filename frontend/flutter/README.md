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

Note: Local loopback URLs (10.0.2.2, localhost, 127.0.0.1) are blocked by default in release builds for security.

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
