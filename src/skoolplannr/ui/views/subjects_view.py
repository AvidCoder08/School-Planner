from typing import Callable, Dict, List
import flet as ft

from skoolplannr.services.firestore_service import FirestoreService
from skoolplannr.state.app_state import AppState


def _parse_schedule_slots(raw: str) -> List[Dict[str, str]]:
    """
    Input format example:
    Mon 10:00-11:00, Wed 14:00-15:00
    """
    slots: List[Dict[str, str]] = []
    if not raw.strip():
        return slots

    entries = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
    for entry in entries:
        parts = entry.split()
        if len(parts) != 2 or "-" not in parts[1]:
            raise ValueError("Invalid schedule format")
        day = parts[0]
        start_time, end_time = parts[1].split("-", maxsplit=1)
        slots.append({"day": day, "start_time": start_time, "end_time": end_time})

    return slots


def build_subjects_view(page: ft.Page, app_state: AppState, on_back: Callable[[], None]) -> ft.View:
    fs = FirestoreService.from_settings()

    name = ft.TextField(label="Subject Name", width=320)
    instructor = ft.TextField(label="Instructor", width=320)
    location = ft.TextField(label="Location", width=320)
    credits = ft.Dropdown(
        width=160,
        label="Credits",
        value="4",
        options=[ft.dropdown.Option("2"), ft.dropdown.Option("4"), ft.dropdown.Option("5")],
    )
    schedule = ft.TextField(
        label="Schedule Slots",
        hint_text="Mon 10:00-11:00, Wed 14:00-15:00",
        width=500,
    )
    status = ft.Text(color=ft.Colors.RED_400)
    list_column = ft.Column(spacing=8)

    def set_status(message: str, is_error: bool = True) -> None:
        status.value = message
        status.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400

    def render_subjects() -> None:
        list_column.controls.clear()
        uid = app_state.session.uid
        if not uid:
            set_status("No active session.")
            page.update()
            return

        subjects = fs.list_subjects(uid)
        if not subjects:
            list_column.controls.append(ft.Text("No subjects added yet."))
            page.update()
            return

        for subject in subjects:
            slots = subject.get("schedule_slots", [])
            slot_text = ", ".join(
                [f"{slot.get('day')} {slot.get('start_time')}-{slot.get('end_time')}" for slot in slots]
            )

            def make_delete_handler(subject_id: str):
                def handler(_):
                    fs.delete_subject(uid, subject_id)
                    set_status("Subject deleted.", is_error=False)
                    render_subjects()
                    page.update()

                return handler

            list_column.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column(
                            controls=[
                                ft.Text(subject.get("name", "Unnamed Subject"), weight=ft.FontWeight.BOLD),
                                ft.Text(f"Instructor: {subject.get('instructor', '-')}, Location: {subject.get('location', '-')}, Credits: {subject.get('credits', '-') }"),
                                ft.Text(f"Slots: {slot_text or '-'}"),
                                ft.Row(
                                    controls=[
                                        ft.TextButton("Delete", on_click=make_delete_handler(subject["id"]))
                                    ]
                                ),
                            ]
                        ),
                    )
                )
            )

        page.update()

    def on_add(_):
        uid = app_state.session.uid
        if not uid:
            set_status("No active session.")
            page.update()
            return

        if not name.value or not credits.value:
            set_status("Subject name and credits are required.")
            page.update()
            return

        try:
            slots = _parse_schedule_slots(schedule.value or "")
            fs.create_subject(
                uid,
                name=name.value.strip(),
                instructor=(instructor.value or "").strip(),
                location=(location.value or "").strip(),
                credits=int(credits.value),
                schedule_slots=slots,
            )
            name.value = ""
            instructor.value = ""
            location.value = ""
            schedule.value = ""
            set_status("Subject added.", is_error=False)
            render_subjects()
        except Exception as exc:
            set_status(f"Failed to add subject: {exc}")
            page.update()

    render_subjects()

    return ft.View(
        route="/subjects",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Subjects")),
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Button("Back to Dashboard", on_click=lambda _: on_back()),
                            ]
                        ),
                        ft.Text("Add Subject", size=22, weight=ft.FontWeight.BOLD),
                        name,
                        instructor,
                        location,
                        credits,
                        schedule,
                        ft.Button("Add Subject", on_click=on_add),
                        status,
                        ft.Divider(),
                        ft.Text("Your Subjects", size=20, weight=ft.FontWeight.BOLD),
                        list_column,
                    ],
                ),
            ),
        ],
    )
