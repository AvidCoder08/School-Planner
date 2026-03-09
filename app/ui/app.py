from __future__ import annotations

from datetime import datetime, timedelta

import flet as ft

from app.domain.logic.gpa import CourseResult, calc_sgpa
from app.domain.logic.grading import calc_subject_final, grade_from_marks
from app.services.storage import Storage

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AcademaSyncApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "AcademaSync"
        self.page.scroll = ft.ScrollMode.AUTO
        self.store = Storage("data/academasync.db")
        self.current_user_id: int | None = None
        self.auth_error = ft.Text(color=ft.Colors.RED)

        self.email = ft.TextField(label="Email", width=300)
        self.password = ft.TextField(label="Password", width=300, password=True, can_reveal_password=True)

    def run(self) -> None:
        self.show_auth_view()

    def show_auth_view(self) -> None:
        self.page.clean()
        self.page.add(
            ft.Column(
                [
                    ft.Text("AcademaSync", size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Sign in or sign up to continue"),
                    self.email,
                    self.password,
                    ft.Row(
                        [
                            ft.ElevatedButton("Sign In", on_click=self.handle_login),
                            ft.OutlinedButton("Sign Up", on_click=self.handle_signup),
                        ]
                    ),
                    self.auth_error,
                ],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def handle_signup(self, _: ft.ControlEvent) -> None:
        try:
            self.current_user_id = self.store.create_user(self.email.value, self.password.value)
            self.show_onboarding()
        except Exception as exc:
            self.auth_error.value = f"Sign up failed: {exc}"
            self.page.update()

    def handle_login(self, _: ft.ControlEvent) -> None:
        user_id = self.store.login_user(self.email.value, self.password.value)
        if user_id is None:
            self.auth_error.value = "Invalid credentials"
            self.page.update()
            return
        self.current_user_id = user_id
        user = self.store.get_user(user_id)
        if user and user["academic_year"]:
            self.show_main_app()
        else:
            self.show_onboarding()

    def show_onboarding(self) -> None:
        year = ft.TextField(label="Academic Year", hint_text="2025-2026")
        sem = ft.TextField(label="Semester Name", hint_text="Fall")
        start = ft.TextField(label="Semester Start (YYYY-MM-DD)")
        end = ft.TextField(label="Semester End (YYYY-MM-DD)")
        error = ft.Text(color=ft.Colors.RED)

        def save(_: ft.ControlEvent) -> None:
            if not self.current_user_id:
                return
            try:
                self.store.update_onboarding(self.current_user_id, year.value, sem.value, start.value, end.value)
                self.show_main_app()
            except Exception as exc:
                error.value = str(exc)
                self.page.update()

        self.page.clean()
        self.page.add(
            ft.Column(
                [
                    ft.Text("Onboarding", size=24, weight=ft.FontWeight.BOLD),
                    year,
                    sem,
                    start,
                    end,
                    ft.ElevatedButton("Save and Continue", on_click=save),
                    error,
                ],
                width=420,
            )
        )

    def show_main_app(self) -> None:
        self.page.clean()

        dashboard_container = ft.Container()
        subjects_container = ft.Container()
        tasks_container = ft.Container()
        grades_container = ft.Container()

        def refresh_all() -> None:
            dashboard_container.content = self.dashboard_view()
            subjects_container.content = self.subjects_view(refresh_all)
            tasks_container.content = self.tasks_view(refresh_all)
            grades_container.content = self.grades_view(refresh_all)
            self.page.update()

        tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Dashboard", content=dashboard_container),
                ft.Tab(text="Subjects", content=subjects_container),
                ft.Tab(text="Tasks", content=tasks_container),
                ft.Tab(text="Grades", content=grades_container),
            ],
            expand=1,
        )

        self.page.add(
            ft.Row(
                [
                    ft.Text("AcademaSync", size=28, weight=ft.FontWeight.BOLD),
                    ft.TextButton("Logout", on_click=lambda _: self.show_auth_view()),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            tabs,
        )
        refresh_all()

    def dashboard_view(self) -> ft.Control:
        assert self.current_user_id is not None
        now = datetime.now()
        today_name = now.strftime("%a")
        subjects = self.store.list_subjects(self.current_user_id)
        today_subjects = [s for s in subjects if s["day_of_week"] == today_name]

        if not today_subjects:
            future = subjects
            current_idx = DAYS.index(today_name) if today_name in DAYS else 0
            next_subjects = []
            for offset in range(1, 8):
                day = DAYS[(current_idx + offset) % 7]
                matches = [s for s in future if s["day_of_week"] == day]
                if matches:
                    next_subjects = matches
                    today_name = day
                    break
            today_subjects = next_subjects

        tasks = self.store.list_tasks(self.current_user_id)
        today = now.date()
        tomorrow = today + timedelta(days=1)
        due_soon = []
        for t in tasks:
            try:
                due = datetime.fromisoformat(t["due_at"]).date()
            except Exception:
                continue
            if due in (today, tomorrow):
                due_soon.append(t)

        timetable_lines = [
            ft.Text(f"• {s['start_time']}-{s['end_time']} {s['name']} @ {s['location']}") for s in today_subjects
        ] or [ft.Text("No scheduled classes")]
        due_lines = [
            ft.Text(f"• {t['title']} ({t['task_type']}) due {t['due_at']}") for t in due_soon
        ] or [ft.Text("No urgent tasks")]

        return ft.Column(
            [
                ft.Text(now.strftime("%A, %d %B %Y • %H:%M"), size=18),
                ft.Text(f"Timetable ({today_name})", size=20, weight=ft.FontWeight.BOLD),
                *timetable_lines,
                ft.Divider(),
                ft.Text("Due Today / Tomorrow", size=20, weight=ft.FontWeight.BOLD),
                *due_lines,
            ]
        )

    def subjects_view(self, refresh_all) -> ft.Control:
        assert self.current_user_id is not None
        name = ft.TextField(label="Subject")
        location = ft.TextField(label="Location")
        instructor = ft.TextField(label="Instructor")
        credits = ft.Dropdown(label="Credits", options=[ft.dropdown.Option(str(c)) for c in (2, 4, 5)], value="4")
        day = ft.Dropdown(label="Day", options=[ft.dropdown.Option(d) for d in DAYS[:6]], value="Mon")
        start = ft.TextField(label="Start", hint_text="10:00")
        end = ft.TextField(label="End", hint_text="11:00")
        error = ft.Text(color=ft.Colors.RED)

        def add_subject(_: ft.ControlEvent) -> None:
            try:
                self.store.add_subject(self.current_user_id, name.value, location.value, instructor.value, int(credits.value), day.value, start.value, end.value)
                refresh_all()
            except Exception as exc:
                error.value = str(exc)
                self.page.update()

        rows = self.store.list_subjects(self.current_user_id)
        list_view = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(f"{r['name']} ({r['credits']} cr) {r['day_of_week']} {r['start_time']}-{r['end_time']}"),
                        ft.IconButton(icon=ft.Icons.DELETE, on_click=lambda _, sid=r["id"]: (self.store.delete_subject(sid, self.current_user_id), refresh_all())),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for r in rows
            ]
        )

        return ft.Column([name, location, instructor, ft.Row([credits, day]), ft.Row([start, end]), ft.ElevatedButton("Add Subject", on_click=add_subject), error, ft.Divider(), list_view])

    def tasks_view(self, refresh_all) -> ft.Control:
        assert self.current_user_id is not None
        title = ft.TextField(label="Task")
        task_type = ft.Dropdown(label="Type", options=[ft.dropdown.Option(x) for x in ["Assignment", "Homework", "Project", "Exam"]], value="Assignment")
        due = ft.TextField(label="Due (YYYY-MM-DDTHH:MM)", hint_text="2026-02-15T23:59")
        subjects = self.store.list_subjects(self.current_user_id)
        subject_options = [ft.dropdown.Option("", "None")] + [ft.dropdown.Option(str(s["id"]), s["name"]) for s in subjects]
        subject_dd = ft.Dropdown(label="Subject", options=subject_options, value="")
        error = ft.Text(color=ft.Colors.RED)

        def add_task(_: ft.ControlEvent) -> None:
            try:
                subject_id = int(subject_dd.value) if subject_dd.value else None
                self.store.add_task(self.current_user_id, title.value, task_type.value, due.value, subject_id)
                refresh_all()
            except Exception as exc:
                error.value = str(exc)
                self.page.update()

        rows = self.store.list_tasks(self.current_user_id)
        list_view = ft.Column(
            [
                ft.Row(
                    [
                        ft.Checkbox(
                            label=f"{r['title']} [{r['task_type']}] due {r['due_at']} ({r['subject_name'] or 'General'})",
                            value=bool(r["is_completed"]),
                            on_change=lambda e, tid=r["id"]: (self.store.toggle_task(tid, self.current_user_id, e.control.value), refresh_all()),
                        ),
                        ft.IconButton(icon=ft.Icons.DELETE, on_click=lambda _, tid=r["id"]: (self.store.delete_task(tid, self.current_user_id), refresh_all())),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
                for r in rows
            ]
        )

        return ft.Column([title, task_type, due, subject_dd, ft.ElevatedButton("Add Task", on_click=add_task), error, ft.Divider(), list_view])

    def grades_view(self, refresh_all) -> ft.Control:
        assert self.current_user_id is not None
        subjects = self.store.list_subjects(self.current_user_id)
        if not subjects:
            return ft.Text("Add subjects first")

        subject_dd = ft.Dropdown(label="Subject", options=[ft.dropdown.Option(str(s["id"]), f"{s['name']} ({s['credits']} cr)") for s in subjects], value=str(subjects[0]["id"]))
        isa1 = ft.TextField(label="ISA1", value="0")
        isa2 = ft.TextField(label="ISA2", value="0")
        esa = ft.TextField(label="ESA", value="0")
        assignments = ft.TextField(label="Assignments", value="0")
        lab = ft.TextField(label="Lab Marks (for 5-credit)", value="0")
        error = ft.Text(color=ft.Colors.RED)

        def save_grade(_: ft.ControlEvent) -> None:
            try:
                sid = int(subject_dd.value)
                subject = next(s for s in subjects if s["id"] == sid)
                self.store.upsert_grade(
                    self.current_user_id,
                    sid,
                    float(isa1.value),
                    float(isa2.value),
                    float(esa.value),
                    float(assignments.value),
                    float(lab.value) if subject["credits"] == 5 else None,
                )
                refresh_all()
            except Exception as exc:
                error.value = str(exc)
                self.page.update()

        rows = self.store.list_grades(self.current_user_id)
        course_results: list[CourseResult] = []
        grade_lines: list[ft.Control] = []
        for r in rows:
            theory_components = [
                (r["isa1"], 50),
                (r["isa2"], 50),
                (r["esa"], 100),
                (r["assignments"], 20),
            ]
            final = calc_subject_final(r["credits"], theory_components, r["lab_marks"], 20)
            letter, gp = grade_from_marks(final)
            course_results.append(CourseResult(credits=r["credits"], grade_point=gp))
            grade_lines.append(ft.Text(f"{r['subject_name']}: {final:.2f}/100 • {letter} • GP {gp}"))

        sgpa = calc_sgpa(course_results)

        return ft.Column(
            [
                subject_dd,
                ft.Row([isa1, isa2]),
                ft.Row([esa, assignments]),
                lab,
                ft.ElevatedButton("Save Marks", on_click=save_grade),
                error,
                ft.Divider(),
                *grade_lines,
                ft.Text(f"Current SGPA: {sgpa:.2f}", size=18, weight=ft.FontWeight.BOLD),
            ]
        )


def main(page: ft.Page) -> None:
    AcademaSyncApp(page).run()
