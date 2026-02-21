from datetime import datetime
from typing import Callable, Dict, List
import flet as ft

from skoolplannr.services.firestore_service import FirestoreService, FirestoreServiceError
from skoolplannr.state.app_state import AppState


DATE_FMT = "%Y-%m-%d"


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value.strip(), DATE_FMT)


def build_onboarding_view(
    page: ft.Page,
    app_state: AppState,
    on_complete: Callable[[], None],
) -> ft.View:
    year_label = ft.TextField(label="Academic Year (e.g., 2025-2026)", width=350)
    year_start = ft.TextField(label="Year Start Date", width=220, read_only=True)
    year_end = ft.TextField(label="Year End Date", width=220, read_only=True)

    term_count = ft.Dropdown(
        label="Number of Terms/Semesters",
        width=220,
        value="2",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 7)],
    )

    term_fields = ft.Column(spacing=10)
    term_inputs: List[Dict[str, ft.Control]] = []

    status_text = ft.Text(color=ft.Colors.RED_400)

    def set_status(message: str, is_error: bool = True) -> None:
        status_text.value = message
        status_text.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400
        page.update()

    def build_term_inputs(count: int) -> None:
        term_inputs.clear()
        term_fields.controls.clear()

        for index in range(count):
            name = ft.TextField(label=f"Term {index + 1} Name", width=350, value=f"Term {index + 1}")
            start = ft.TextField(label=f"Term {index + 1} Start Date", width=220, read_only=True)
            end = ft.TextField(label=f"Term {index + 1} End Date", width=220, read_only=True)

            start_picker = ft.DatePicker()
            end_picker = ft.DatePicker()

            def make_start_handler(field: ft.TextField, picker: ft.DatePicker):
                def handler(_):
                    if picker.value:
                        field.value = picker.value.strftime(DATE_FMT)
                        page.update()

                return handler

            def make_end_handler(field: ft.TextField, picker: ft.DatePicker):
                def handler(_):
                    if picker.value:
                        field.value = picker.value.strftime(DATE_FMT)
                        page.update()

                return handler

            start_picker.on_change = make_start_handler(start, start_picker)
            end_picker.on_change = make_end_handler(end, end_picker)

            page.overlay.extend([start_picker, end_picker])

            def make_open_handler(picker: ft.DatePicker):
                def handler(_):
                    picker.open = True
                    page.update()

                return handler

            start.on_focus = make_open_handler(start_picker)
            end.on_focus = make_open_handler(end_picker)

            term_inputs.append({"name": name, "start": start, "end": end})
            term_fields.controls.extend([name, start, end, ft.Divider()])

        if term_fields.controls:
            term_fields.controls.pop()
        page.update()

    def on_term_count_change(_):
        try:
            count = int(term_count.value or "1")
        except ValueError:
            count = 1
        build_term_inputs(count)

    def on_save(_):
        if not app_state.session.uid:
            set_status("No active session found. Please log in again.")
            return

        required = [year_label.value, year_start.value, year_end.value]
        for term in term_inputs:
            required.extend([term["name"].value, term["start"].value, term["end"].value])

        if not all(required):
            set_status("Please fill all onboarding fields.")
            return

        try:
            ys = _parse_date(year_start.value)
            ye = _parse_date(year_end.value)
        except ValueError:
            set_status("Date format must be YYYY-MM-DD.")
            return

        if ys > ye:
            set_status("Year start date must be before end date.")
            return

        terms_payload = []
        for term in term_inputs:
            try:
                ts = _parse_date(term["start"].value)
                te = _parse_date(term["end"].value)
            except ValueError:
                set_status("Date format must be YYYY-MM-DD.")
                return

            if ts > te:
                set_status("Term start date must be before end date.")
                return

            if ts < ys or te > ye:
                set_status("Term dates must be within the academic year.")
                return

            terms_payload.append(
                {
                    "name": term["name"].value.strip(),
                    "start_date": ts,
                    "end_date": te,
                }
            )

        try:
            fs = FirestoreService.from_settings()
            fs.save_onboarding(
                uid=app_state.session.uid,
                year_label=year_label.value.strip(),
                year_start=ys,
                year_end=ye,
                terms=terms_payload,
            )
            set_status("Onboarding saved.", is_error=False)
            on_complete()
        except FirestoreServiceError as exc:
            set_status(f"Firestore config error: {exc}")
        except Exception as exc:
            set_status(f"Failed to save onboarding: {exc}")

    term_count.on_change = on_term_count_change
    build_term_inputs(int(term_count.value or "2"))

    year_start_picker = ft.DatePicker()
    year_end_picker = ft.DatePicker()

    def on_year_start_change(_):
        if year_start_picker.value:
            year_start.value = year_start_picker.value.strftime(DATE_FMT)
            page.update()

    def on_year_end_change(_):
        if year_end_picker.value:
            year_end.value = year_end_picker.value.strftime(DATE_FMT)
            page.update()

    year_start_picker.on_change = on_year_start_change
    year_end_picker.on_change = on_year_end_change

    page.overlay.extend([year_start_picker, year_end_picker])

    def make_open_year_picker(picker: ft.DatePicker):
        def handler(_):
            picker.open = True
            page.update()

        return handler

    year_start.on_focus = make_open_year_picker(year_start_picker)
    year_end.on_focus = make_open_year_picker(year_end_picker)

    return ft.View(
        route="/onboarding",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Onboarding")),
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Text("Set up your academic year", size=26, weight=ft.FontWeight.BOLD),
                        year_label,
                        year_start,
                        year_end,
                        ft.Divider(),
                        term_count,
                        term_fields,
                        ft.Button("Save & Continue", on_click=on_save),
                        status_text,
                    ],
                ),
            ),
        ],
    )


