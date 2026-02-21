# SkoolPlannr Project Summary

## Overview
SkoolPlannr is a multi-platform student planner and grade tracker built with Python and Flet, backed by Firebase Authentication and Firestore. The app centralizes schedules, tasks, grades, and performance analytics, with Windows/Web/Android/iOS as target platforms.

## Product Requirements (Condensed)
- Auth: Email/password signup + login with secure, per-user data isolation.
- Onboarding: Academic year setup, terms/semesters with start/end dates.
- Dashboard: Current date/time, today or next-day timetable, due tasks, and upcoming events.
- Subjects: CRUD with instructor, location, credits, and schedule slots.
- Tasks: CRUD with due date/time, priority, completion.
- Calendar: Events for classes/exams/holidays/deadlines.
- Grades: Assessment entry for 2/4/5 credit rules, final score, letter grade, grade points.
- SGPA/CGPA: Automatic calculation and trend tracking.

## Architecture
### Frontend
- Flet UI with route-based views:
  - Login
  - Onboarding
  - Dashboard (Today view)
  - Subjects
  - Tasks
  - Calendar
  - Grades

### Backend
- Firebase Authentication (Email/Password via REST API).
- Firestore database with user-scoped collections.

### Data Model (High Level)
- users/{uid}
  - academic_years/{year_id}
    - terms/{term_id}
      - subjects/{subject_id}
        - assessments/{assessment_id}
      - tasks/{task_id}
      - events/{event_id}
      - grades/{subject_id}

## Current Implementation Status
### Completed
- Auth (Email/Password) and onboarding flow.
- Onboarding supports multiple terms with date pickers.
- Subjects CRUD and schedule slots.
- Tasks CRUD and completion toggles.
- Calendar events CRUD.
- Dashboard with:
  - today/next-day timetable
  - due tasks (today/tomorrow)
  - upcoming events summary
  - SGPA/CGPA summary
- Grade calculator with assessment inputs.
- SGPA/CGPA calculations and SGPA trend list.
- Firestore services for subjects, tasks, events, grades, and onboarding.

### In Progress / Next Up
- Calendar week/month visualization.
- Grade editing per assessment after save.
- Subject/term switching and historical term views.
- Push notifications and offline cache.

## Key Files
- App entrypoint: src/skoolplannr/app.py
- Firestore integration: src/skoolplannr/services/firestore_service.py
- Grade logic: src/skoolplannr/core/grades.py
- GPA logic: src/skoolplannr/core/gpa.py
- Views:
  - src/skoolplannr/ui/views/login_view.py
  - src/skoolplannr/ui/views/onboarding_view.py
  - src/skoolplannr/ui/views/dashboard_view.py
  - src/skoolplannr/ui/views/subjects_view.py
  - src/skoolplannr/ui/views/tasks_view.py
  - src/skoolplannr/ui/views/events_view.py
  - src/skoolplannr/ui/views/grades_view.py

## How to Run (Windows)
1. Double-click run.bat.
2. Ensure .env is configured with:
   - FIREBASE_API_KEY
   - FIREBASE_PROJECT_ID
   - GOOGLE_APPLICATION_CREDENTIALS

## Security & Policy Notes
- Firestore rules enforce per-user data isolation under users/{uid}.
- Password policy: minimum length 8, uppercase/lowercase/numeric/special required, require enforcement enabled.

## Technical Notes
- Requirements pinned for Flet compatibility (flet==0.80.5).
- Pydantic marked optional due to Python 3.14 wheel availability.
