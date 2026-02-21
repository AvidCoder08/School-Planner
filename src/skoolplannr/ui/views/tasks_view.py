from datetime import datetime
from typing import Callable, Optional
import flet as ft

from skoolplannr.services.firestore_service import FirestoreService
from skoolplannr.state.app_state import AppState


DATE_TIME_FMT = "%Y-%m-%d %H:%M"


def build_tasks_view(page: ft.Page, app_state: AppState, on_back: Callable[[], None]) -> ft.View:
    fs = FirestoreService.from_settings()

    title = ft.TextField(label="Task Title", width=350)
    description = ft.TextField(label="Description", width=500, multiline=True, min_lines=2, max_lines=4)
    due_at = ft.TextField(label="Due (YYYY-MM-DD HH:MM)", width=260)
    task_type = ft.Dropdown(
        width=220,
        label="Task Type",
        value="assignment",
        options=[
            ft.dropdown.Option("assignment"),
            ft.dropdown.Option("homework"),
            ft.dropdown.Option("project"),
            ft.dropdown.Option("exam"),
        ],
    )
    priority = ft.Dropdown(
        width=180,
        label="Priority",
        value="medium",
        options=[ft.dropdown.Option("low"), ft.dropdown.Option("medium"), ft.dropdown.Option("high")],
    )
    subject = ft.Dropdown(width=320, label="Subject (optional)")
    status = ft.Text(color=ft.Colors.RED_400)
    task_list = ft.Column(spacing=8)

    def set_status(message: str, is_error: bool = True) -> None:
        status.value = message
        status.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400

    def _subject_id() -> Optional[str]:
        value = subject.value or ""
        return value if value else None

    def refresh_subject_options() -> None:
        uid = app_state.session.uid
        if not uid:
            return

        subjects = fs.list_subjects(uid)
        options = [ft.dropdown.Option("", "No subject")]
        options.extend([ft.dropdown.Option(s["id"], s.get("name", s["id"])) for s in subjects])
        subject.options = options
        if subject.value and all(opt.key != subject.value for opt in options):
            subject.value = ""

    def refresh_tasks() -> None:
        uid = app_state.session.uid
        if not uid:
            set_status("No active session.")
            page.update()
            return

        task_list.controls.clear()
        tasks = fs.list_tasks(uid, include_completed=True)

        if not tasks:
            task_list.controls.append(ft.Text("No tasks added yet."))
            page.update()
            return

        for task in tasks:
            due = task.get("due_at")
            due_text = due.strftime(DATE_TIME_FMT) if hasattr(due, "strftime") else "-"

            def make_toggle_handler(task_id: str, current: bool):
                def handler(_):
                    fs.set_task_completed(uid, task_id, not current)
                    refresh_tasks()
                    page.update()

                return handler

            def make_delete_handler(task_id: str):
                def handler(_):
                    fs.delete_task(uid, task_id)
                    refresh_tasks()
                    page.update()

                return handler

            task_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Column(
                            controls=[
                                ft.Text(task.get("title", "Untitled Task"), weight=ft.FontWeight.BOLD),
                                ft.Text(f"Type: {task.get('task_type', '-')}, Priority: {task.get('priority', '-')}, Due: {due_text}"),
                                ft.Text(f"Completed: {task.get('completed', False)}"),
                                ft.Text(task.get("description", "")),
                                ft.Row(
                                    controls=[
                                        ft.TextButton(
                                            "Mark Pending" if task.get("completed") else "Mark Completed",
                                            on_click=make_toggle_handler(task["id"], bool(task.get("completed"))),
                                        ),
                                        ft.TextButton("Delete", on_click=make_delete_handler(task["id"])),
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

        if not title.value or not due_at.value:
            set_status("Task title and due date/time are required.")
            page.update()
            return

        try:
            parsed_due = datetime.strptime(due_at.value.strip(), DATE_TIME_FMT)
            fs.create_task(
                uid,
                title=title.value.strip(),
                description=(description.value or "").strip(),
                subject_id=_subject_id(),
                task_type=(task_type.value or "assignment"),
                due_at=parsed_due,
                priority=(priority.value or "medium"),
            )
            title.value = ""
            description.value = ""
            due_at.value = ""
            subject.value = ""
            set_status("Task added.", is_error=False)
            refresh_tasks()
        except ValueError:
            set_status("Invalid date format. Use YYYY-MM-DD HH:MM.")
            page.update()
        except Exception as exc:
            set_status(f"Failed to add task: {exc}")
            page.update()

    refresh_subject_options()
    refresh_tasks()

    return ft.View(
        route="/tasks",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Tasks")),
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Row(controls=[ft.Button("Back to Dashboard", on_click=lambda _: on_back())]),
                        ft.Text("Add Task", size=22, weight=ft.FontWeight.BOLD),
                        title,
                        description,
                        ft.Row(controls=[due_at, task_type, priority]),
                        subject,
                        ft.Button("Add Task", on_click=on_add),
                        status,
                        ft.Divider(),
                        ft.Text("Your Tasks", size=20, weight=ft.FontWeight.BOLD),
                        task_list,
                    ],
                ),
            ),
        ],
    )
