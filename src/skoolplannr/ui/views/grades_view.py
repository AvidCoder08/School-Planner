from typing import Callable, Dict
import flet as ft

from skoolplannr.core.grades import RULES_BY_CREDITS
from skoolplannr.services.firestore_service import FirestoreService, FirestoreServiceError
from skoolplannr.state.app_state import AppState


def _build_bar(value: float) -> ft.Container:
    width = max(10, int(220 * (value / 10)))
    return ft.Container(width=width, height=12, bgcolor=ft.Colors.BLUE_400, border_radius=6)


def build_grades_view(page: ft.Page, app_state: AppState, on_back: Callable[[], None]) -> ft.View:
    fs = FirestoreService.from_settings()

    subject = ft.Dropdown(width=360, label="Subject")
    status = ft.Text(color=ft.Colors.RED_400)
    summary_text = ft.Text()
    sgpa_text = ft.Text()
    cgpa_text = ft.Text()

    assessment_fields = ft.Column(spacing=10)
    grades_list = ft.Column(spacing=8)
    trend_list = ft.Column(spacing=6)

    subject_map: Dict[str, Dict] = {}
    field_map: Dict[str, ft.TextField] = {}

    def set_status(message: str, is_error: bool = True) -> None:
        status.value = message
        status.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400

    def load_subjects() -> None:
        uid = app_state.session.uid
        if not uid:
            return
        subjects = fs.list_subjects(uid)
        subject_map.clear()
        options = []
        for subj in subjects:
            subject_map[subj["id"]] = subj
            options.append(ft.dropdown.Option(subj["id"], subj.get("name", subj["id"])))
        subject.options = options
        if subject.value and subject.value not in subject_map:
            subject.value = None

    def load_existing_scores(subject_id: str) -> Dict[str, float]:
        uid = app_state.session.uid
        if not uid:
            return {}
        return fs.get_assessments(uid, subject_id)

    def build_assessment_fields() -> None:
        assessment_fields.controls.clear()
        field_map.clear()

        subject_id = subject.value
        if not subject_id or subject_id not in subject_map:
            page.update()
            return

        credits = int(subject_map[subject_id].get("credits", 0))
        if credits not in RULES_BY_CREDITS:
            set_status("Unsupported credit model.")
            page.update()
            return

        existing = load_existing_scores(subject_id)
        for name, rule in RULES_BY_CREDITS[credits].items():
            field = ft.TextField(
                label=f"{name} (out of {rule.max_raw})",
                width=280,
                value=str(existing.get(name, "")) if existing else "",
            )
            field_map[name] = field
            assessment_fields.controls.append(field)

        page.update()

    def refresh_grade_list() -> None:
        grades_list.controls.clear()
        uid = app_state.session.uid
        if not uid:
            return
        grades = fs.list_grades(uid)
        if not grades:
            grades_list.controls.append(ft.Text("No grade records yet."))
        else:
            for grade in grades:
                grades_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=12,
                            content=ft.Column(
                                controls=[
                                    ft.Text(grade.get("subject_name", "Subject"), weight=ft.FontWeight.BOLD),
                                    ft.Text(
                                        f"Score: {grade.get('final_score_100', '-')}, "
                                        f"Letter: {grade.get('letter_grade', '-')}, "
                                        f"Point: {grade.get('grade_point', '-')}, "
                                        f"Credits: {grade.get('credits', '-')}"
                                    ),
                                ]
                            ),
                        )
                    )
                )

    def refresh_trend() -> None:
        trend_list.controls.clear()
        uid = app_state.session.uid
        if not uid:
            return

        try:
            _, trend = fs.calculate_and_store_cgpa(uid)
        except FirestoreServiceError:
            trend = []

        if not trend:
            trend_list.controls.append(ft.Text("No SGPA trend yet."))
            return

        for entry in trend:
            label = entry.get("label", "Term")
            sgpa = float(entry.get("sgpa", 0))
            trend_list.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(label, width=220),
                        _build_bar(sgpa),
                        ft.Text(f"{sgpa:.2f}"),
                    ]
                )
            )

    def update_sgpa_cgpa() -> None:
        uid = app_state.session.uid
        if not uid:
            return
        try:
            sgpa, credits = fs.calculate_and_store_sgpa(uid)
            sgpa_text.value = f"SGPA (current term): {sgpa:.2f} (credits: {credits})"
        except FirestoreServiceError:
            sgpa_text.value = "SGPA (current term): -"

        cgpa = fs.get_cached_cgpa(uid)
        if cgpa is not None:
            cgpa_text.value = f"CGPA: {cgpa:.2f}"
        else:
            cgpa_text.value = "CGPA: -"

    def on_calculate(_):
        uid = app_state.session.uid
        if not uid:
            set_status("No active session.")
            page.update()
            return

        subject_id = subject.value
        if not subject_id:
            set_status("Select a subject first.")
            page.update()
            return

        raw_scores: Dict[str, float] = {}
        try:
            for name, field in field_map.items():
                val = field.value.strip() if field.value else ""
                if val:
                    raw_scores[name] = float(val)

            grade_doc = fs.save_assessments_and_grade(uid, subject_id, raw_scores)
            
            if grade_doc.get("partial"):
                missing_str = ", ".join(grade_doc.get("missing", []))
                summary_text.value = f"Partial assessments saved. Missing: {missing_str}"
                set_status("Partial save successful.", is_error=False)
            else:
                summary_text.value = (
                    f"Final Score: {grade_doc.get('final_score_100', '-')} | "
                    f"Letter: {grade_doc.get('letter_grade', '-')} | "
                    f"Point: {grade_doc.get('grade_point', '-')}"
                )
                set_status("Grade saved.", is_error=False)

            update_sgpa_cgpa()
            refresh_grade_list()
            refresh_trend()
        except Exception as exc:
            set_status(f"Failed to calculate: {exc}")

        page.update()

    def on_subject_change(_):
        build_assessment_fields()

    subject.on_change = on_subject_change

    load_subjects()
    update_sgpa_cgpa()
    refresh_grade_list()
    refresh_trend()

    return ft.View(
        route="/grades",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Grades")),
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Row(controls=[ft.Button("Back to Dashboard", on_click=lambda _: on_back())]),
                        ft.Text("Grade Calculator", size=22, weight=ft.FontWeight.BOLD),
                        subject,
                        assessment_fields,
                        ft.Button("Calculate & Save", on_click=on_calculate),
                        status,
                        summary_text,
                        ft.Divider(),
                        ft.Text("SGPA / CGPA", size=20, weight=ft.FontWeight.BOLD),
                        sgpa_text,
                        cgpa_text,
                        ft.Button("Recalculate CGPA", on_click=lambda _: refresh_trend()),
                        ft.Divider(),
                        ft.Text("SGPA Trend", size=20, weight=ft.FontWeight.BOLD),
                        trend_list,
                        ft.Divider(),
                        ft.Text("Grade Records", size=20, weight=ft.FontWeight.BOLD),
                        grades_list,
                    ],
                ),
            ),
        ],
    )
