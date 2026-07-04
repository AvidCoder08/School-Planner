# F-Droid Release Notes

This project has been prepared for open-source Android distribution.

## What was changed

- Android release signing is optional for CI/F-Droid builds.
- Private local signing file is no longer tracked.
- A template is provided at `frontend/flutter/android/key.properties.example`.
- App listing metadata was added at `frontend/flutter/fastlane/metadata/android/en-US/`.

## Build commands

Run from `frontend/flutter`:

```bash
flutter pub get
flutter build apk --release
```

Or for AAB:

```bash
flutter build appbundle --release
```

## Important for maintainers

- Keep `frontend/flutter/android/key.properties` local only.
- Keep all credentials out of git history.
- If you rotate secrets, do not commit them.

## Suggested F-Droid metadata fields

Use the files in `fastlane/metadata/android/en-US/` as the baseline text for:
- Title
- Short description
- Full description
- Changelog
