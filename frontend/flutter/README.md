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
The app uses `http://localhost:8555` by default.

To override, pass a Dart define:
```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8555
```
