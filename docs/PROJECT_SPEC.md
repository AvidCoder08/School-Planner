# AcademaSync — Multi-Platform Student Planner & Grade Tracker

## 1) Project Vision & Goals

**AcademaSync** is intended to be a central academic hub for university/college students.

### Target user
- Students managing complex schedules, assignments, exams, and grading patterns.

### Core objectives
- Centralize schedule, tasks, and grades.
- Provide timely reminders and clear daily/weekly views.
- Automate SGPA/CGPA and per-subject grade calculations.
- Deliver a consistent experience on Windows, Web, and Android.

---

## 2) Core Feature Requirements (User Stories)

### Module 1: Authentication & Onboarding
- As a new user, I can sign up with email/password so data is securely synced.
- As a returning user, I can sign in and access my existing records.
- As a first-time user, I complete onboarding to define academic year, semester names, and start/end dates.

### Module 2: Dashboard (“Today” view)
- I can see today’s timetable when opening the app.
- If today’s classes are over, I see the next scheduled day automatically.
- I can view tasks due today/tomorrow.
- I can see current date/time prominently.

### Module 3: Course & Schedule Management
- I can add/edit/delete subjects with:
  - subject name
  - location
  - instructor
  - credits (2/4/5)
  - class timings (multi-day slots)
- I can view a consolidated calendar for classes, exams, deadlines, and holidays.

### Module 4: Task Management
- I can add/edit/delete tasks (assignment/homework/project milestone/exam).
- Each task supports due date/time, subject link, and completion status.

### Module 5: Grade Calculation & Tracking
- I can enter marks for each assessment under a subject.
- The app computes final subject marks out of 100 using credit-specific rules.

#### Grade calculation logic
- **2 & 4 credits**: weighted sum according to each subject’s configured assessment components.
- **5 credits**: theory + lab blend:

```text
final = ((ISA1 + ISA2 + ESA + Assignments) / 220 * 100) * 0.80
      + (Lab_Marks / 20 * 100) * 0.20
```

> Note: This formula is valid if the theory maximum is 220 and lab maximum is 20, and final weighting is 80/20.

#### Letter-grade conversion
| Letter | Marks | Grade Point |
|---|---|---|
| S | 90–100 | 10 |
| A | 80–89 | 9 |
| B | 70–79 | 8 |
| C | 60–69 | 7 |
| D | 50–59 | 6 |
| E | 40–49 | 5 |
| F | 0–39 | 4 |

#### SGPA and CGPA
- **SGPA** for semester:

```text
SGPA = Σ(course_credits × course_grade_point) / Σ(total_credits)
```

- **CGPA** across semesters:

```text
CGPA = Σ(all_course_credits × all_course_grade_points) / Σ(all_course_credits)
```

- Visual analytics: SGPA trend by semester + CGPA progression chart.

---

## 3) Technical Stack

- **Frontend/UI**: Flet (Python)
- **Backend/Auth/DB**: Firebase Authentication + Firestore
- **Language**: Python
- **Platforms**: Windows, Web, Android

---

## 4) Firebase Setup Instructions

1. Create a Firebase project in Firebase Console.
2. Add app registrations as needed (Web first; Android later).
3. Enable **Authentication → Sign-in method → Email/Password**.
4. Create Firestore in production mode (or test mode for early local prototyping).
5. Configure baseline security rules for user-scoped data.

Example baseline Firestore rules (user-owned model):

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId}/{document=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Optional: top-level public config docs
    match /public/{document=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

6. Store Firebase config/credentials via environment variables; avoid committing secrets.

---

## 5) Firestore Schema Proposal

A user-rooted hierarchy keeps authorization simple.

```text
users/{uid}
  profile: {
    name,
    email,
    created_at,
    timezone
  }
  academic_years/{yearId}
    data: { label: "2023-2024", is_active: true }
    semesters/{semesterId}
      data: {
        name,
        start_date,
        end_date,
        order,
        sgpa
      }
      subjects/{subjectId}
        data: {
          name,
          instructor,
          location,
          credits,
          schedule_slots: [
            { day: "Mon", start: "10:00", end: "11:00" }
          ],
          grading_template_id
        }
        assessments/{assessmentId}
          data: {
            name,
            max_marks,
            weight,
            obtained_marks,
            component_type  // theory/lab/etc
          }
      tasks/{taskId}
        data: {
          title,
          type,
          subject_id,
          due_at,
          is_completed,
          priority,
          notes
        }
      events/{eventId}
        data: {
          title,
          kind, // class/exam/holiday/deadline
          starts_at,
          ends_at,
          subject_id?
        }
```

---

## 6) Suggested Python/Flet Project Structure

```text
school_planner/
  app/
    main.py
    config.py
    routes.py
    state/
      app_state.py
      session_state.py
    ui/
      pages/
        login_page.py
        onboarding_page.py
        dashboard_page.py
        subjects_page.py
        tasks_page.py
        grades_page.py
        analytics_page.py
      components/
        timetable_card.py
        task_list.py
        grade_table.py
        chart_panel.py
    services/
      firebase_auth_service.py
      firestore_service.py
      notification_service.py
      sync_service.py
    domain/
      models/
        user.py
        semester.py
        subject.py
        task.py
        assessment.py
      logic/
        grading.py
        gpa.py
        schedule.py
    repositories/
      semester_repository.py
      subject_repository.py
      task_repository.py
      grade_repository.py
  tests/
    test_grading.py
    test_gpa.py
  requirements.txt
  .env.example
```

---

## 7) Core Logic Snippets (Python)

```python
from dataclasses import dataclass
from typing import Iterable, Tuple

GRADE_BANDS: list[Tuple[int, int, str, int]] = [
    (90, 100, "S", 10),
    (80, 89, "A", 9),
    (70, 79, "B", 8),
    (60, 69, "C", 7),
    (50, 59, "D", 6),
    (40, 49, "E", 5),
    (0, 39, "F", 4),
]


def clamp_0_100(value: float) -> float:
    return max(0.0, min(100.0, value))


def grade_from_marks(marks: float) -> tuple[str, int]:
    m = int(round(clamp_0_100(marks)))
    for lo, hi, letter, point in GRADE_BANDS:
        if lo <= m <= hi:
            return letter, point
    return "F", 4


def calc_weighted_total(components: Iterable[tuple[float, float]]) -> float:
    """
    components: iterable of (obtained_marks, max_marks)
    Returns percentage out of 100 by normalized aggregate.
    """
    obtained_sum = 0.0
    max_sum = 0.0
    for obtained, max_marks in components:
        obtained_sum += obtained
        max_sum += max_marks
    if max_sum <= 0:
        return 0.0
    return clamp_0_100((obtained_sum / max_sum) * 100.0)


def calc_subject_final(
    credits: int,
    theory_components: Iterable[tuple[float, float]],
    lab_marks: float | None = None,
    lab_max: float = 20.0,
) -> float:
    """
    - credits 2/4: normalized weighted total from provided components.
    - credits 5: 80% theory + 20% lab.
    """
    theory_pct = calc_weighted_total(theory_components)

    if credits in (2, 4):
        return theory_pct

    if credits == 5:
        if lab_marks is None or lab_max <= 0:
            raise ValueError("lab_marks and valid lab_max are required for 5-credit subjects")
        lab_pct = clamp_0_100((lab_marks / lab_max) * 100.0)
        return clamp_0_100(theory_pct * 0.80 + lab_pct * 0.20)

    raise ValueError("Unsupported credits. Expected 2, 4, or 5.")


@dataclass
class CourseResult:
    credits: int
    grade_point: int


def calc_sgpa(courses: Iterable[CourseResult]) -> float:
    weighted = 0.0
    total_credits = 0
    for c in courses:
        weighted += c.credits * c.grade_point
        total_credits += c.credits
    if total_credits == 0:
        return 0.0
    return round(weighted / total_credits, 2)


def calc_cgpa(semester_course_sets: Iterable[Iterable[CourseResult]]) -> float:
    weighted = 0.0
    total_credits = 0
    for sem_courses in semester_course_sets:
        for c in sem_courses:
            weighted += c.credits * c.grade_point
            total_credits += c.credits
    if total_credits == 0:
        return 0.0
    return round(weighted / total_credits, 2)
```

---

## 8) Phased Development Plan

1. **Foundation**
   - Initialize Python project, Flet app shell, environment config, lint/format setup.
2. **Auth + Session**
   - Firebase Email/Password auth, login/signup, token/session persistence, route guards.
3. **Onboarding + Academic Structure**
   - Academic year and semester setup flow.
4. **Subjects + Timetable**
   - Subject CRUD, recurring schedule slots, “today/next-day” timetable logic.
5. **Tasks + Calendar**
   - Task CRUD, due filters (today/tomorrow), exam/holiday/deadline events.
6. **Grades + GPA**
   - Assessment entry, per-subject mark calculation, grade mapping, SGPA/CGPA.
7. **Dashboard + Analytics**
   - Unified dashboard cards, trend charts.
8. **Sync, Notifications, Hardening**
   - Push/local reminders, offline caching strategy, rule tightening, QA pass.
9. **Packaging/Release**
   - Web deployment + Windows packaging + Android distribution pipeline.

---

## 9) Additional Recommendations

- **State management:** central app/session state + page-level view models.
- **Data validation:** use `pydantic` models for payload validation.
- **Dependency hygiene:** lock dependencies and keep `requirements.txt` curated.
- **Offline strategy:** local cache (SQLite or local file cache) with sync reconciliation.
- **Observability:** structured logging + lightweight crash/error reporting.
- **Testing:** prioritize domain logic unit tests (grading/GPA/date handling).
- **Security:** strict Firestore rules; never embed admin credentials in client app.
