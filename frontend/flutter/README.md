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

For Android emulator local backend testing, use:
```bash
flutter run -d emulator-5554 --dart-define=API_BASE_URL=http://10.0.2.2:8555
```
