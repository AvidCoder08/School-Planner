from datetime import datetime, timedelta
from typing import Callable, Dict, List
import flet as ft
from google.cloud.firestore_v1.base_client import BaseClient # Just for type checking, maybe unnecessary
import json

from skoolplannr.services.firestore_service import FirestoreService
from skoolplannr.state.app_state import AppState


DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _to_minutes(value: str) -> int:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour) * 60 + int(minute)


def _day_from_date(date_obj: datetime) -> str:
    return DAY_NAMES[date_obj.weekday()]


def _schedule_map(subjects: List[Dict]) -> Dict[str, List[Dict]]:
    mapping: Dict[str, List[Dict]] = {day: [] for day in DAY_NAMES}
    for subject in subjects:
        for slot in subject.get("schedule_slots", []):
            day = slot.get("day")
            if day not in mapping:
                continue
            mapping[day].append(
                {
                    "subject_name": subject.get("name", "Unnamed Subject"),
                    "location": subject.get("location", "-"),
                    "start_time": slot.get("start_time", "00:00"),
                    "end_time": slot.get("end_time", "00:00"),
                }
            )

    for day in DAY_NAMES:
        mapping[day].sort(key=lambda row: row["start_time"])
    return mapping


def _pick_schedule_day(now: datetime, schedule_by_day: Dict[str, List[Dict]]) -> datetime:
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_key = _day_from_date(now)
    today_slots = schedule_by_day.get(today_key, [])

    if today_slots:
        latest_end = max(_to_minutes(slot["end_time"]) for slot in today_slots)
        now_minutes = now.hour * 60 + now.minute
        if now_minutes <= latest_end:
            return today

    for offset in range(1, 8):
        probe = today + timedelta(days=offset)
        probe_key = _day_from_date(probe)
        if schedule_by_day.get(probe_key):
            return probe

    return today


def build_dashboard_view(
    page: ft.Page,
    app_state: AppState,
    on_manage_subjects: Callable[[], None],
    on_manage_tasks: Callable[[], None],
    on_manage_calendar: Callable[[], None],
    on_manage_grades: Callable[[], None],
    on_logout: Callable[[], None],
) -> ft.View:
    fs = FirestoreService.from_settings()
    offline_banner = ft.Container(visible=False)

    try:
        if uid:
            subjects = fs.list_subjects(uid)
            tasks = fs.list_tasks(uid, include_completed=False)
            events = fs.list_events(uid)
            term_summary = fs.get_active_term_summary(uid)
            cgpa_value = fs.get_cached_cgpa(uid)
            
            # Helper to serialize datetimes
            def _dt_to_str(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
            
            # Quick serializer for nested dicts with dates
            def serialize_list(lst):
                res = []
                for item in lst:
                    res.append({k: _dt_to_str(v) for k, v in item.items()})
                return res

            cache_data = {
                "subjects": serialize_list(subjects),
                "tasks": serialize_list(tasks),
                "events": serialize_list(events),
                "term_summary": {k: _dt_to_str(v) for k, v in term_summary.items()},
                "cgpa_value": cgpa_value
            }
            page.client_storage.set("dashboard_cache", cache_data)
        else:
            subjects, tasks, events, term_summary, cgpa_value = [], [], [], {}, None
            
    except Exception as e:
        print(f"Network error, falling back to cache. Exception: {e}")
        offline_banner = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.WIFI_OFF, color=ft.Colors.WHITE),
                ft.Text("You are offline. Showing cached data.", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.RED_800,
            padding=10,
            border_radius=5,
            margin=ft.margin.only(bottom=10)
        )
        
        cached = page.client_storage.get("dashboard_cache")
        if cached:
             # Helper to restore datetimes
             def _str_to_dt(val):
                 if isinstance(val, str) and "T" in val:
                     try:
                         return datetime.fromisoformat(val)
                     except ValueError:
                         return val
                 return val
             
             def restore_list(lst):
                 res = []
                 for item in lst:
                     res.append({k: _str_to_dt(v) for k, v in item.items()})
                 return res

             subjects = restore_list(cached.get("subjects", []))
             tasks = restore_list(cached.get("tasks", []))
             events = restore_list(cached.get("events", []))
             term_summary = {k: _str_to_dt(v) for k, v in cached.get("term_summary", {}).items()}
             cgpa_value = cached.get("cgpa_value")
        else:
             subjects, tasks, events, term_summary, cgpa_value = [], [], [], {}, None

    sgpa_value = term_summary.get("sgpa")

    schedule_by_day = _schedule_map(subjects)
    target_day_date = _pick_schedule_day(now, schedule_by_day)
    target_day_name = _day_from_date(target_day_date)
    target_slots = schedule_by_day.get(target_day_name, [])

    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_tomorrow = (start_today + timedelta(days=2)) - timedelta(microseconds=1)

    due_tasks = []
    for task in tasks:
        due_at = task.get("due_at")
        if hasattr(due_at, "replace") and start_today <= due_at <= end_tomorrow:
            due_tasks.append(task)
    due_tasks.sort(key=lambda row: row.get("due_at"))

    active_profile = fs.get_profile(uid) if uid else {}
    active_year_id = active_profile.get("active_year_id")
    active_term_id = active_profile.get("active_term_id")
    
    term_dropdown = ft.Dropdown(
        width=300, 
        label="Select Term",
        on_change=lambda e: _on_term_change(e.control.value)
    )

    def _on_term_change(json_value: str):
        if not json_value:
             return
        data = json.loads(json_value)
        new_year_id = data["year_id"]
        new_term_id = data["term_id"]
        if new_year_id and new_term_id and uid:
             fs.set_active_term(uid, new_year_id, new_term_id)
             page.go("/dashboard")

    if uid:
        try:
            years_data = fs.list_years_and_terms(uid)
            options = []
            selected_val = None
            for y in years_data:
                for t in y.get("terms", []):
                    val = json.dumps({"year_id": y["id"], "term_id": t["id"]})
                    options.append(
                        ft.dropdown.Option(val, f"{y['label']} - {t['name']}")
                    )
                    if y["id"] == active_year_id and t["id"] == active_term_id:
                        selected_val = val
            term_dropdown.options = options
            term_dropdown.value = selected_val
        except Exception as e:
            print("Error loading terms for dropdown:", e)

    class_controls = []
    if target_slots:
        for slot in target_slots:
            class_controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            controls=[
                                ft.Text(slot["subject_name"], weight=ft.FontWeight.BOLD),
                                ft.Text(f"{slot['start_time']} - {slot['end_time']}"),
                                ft.Text(f"Location: {slot['location']}"),
                            ]
                        ),
                    )
                )
            )
    else:
        class_controls.append(ft.Text("No scheduled classes found."))

    task_controls = []
    if due_tasks:
        for task in due_tasks:
            due_at = task.get("due_at")
            due_text = due_at.strftime("%Y-%m-%d %H:%M") if hasattr(due_at, "strftime") else "-"
            task_controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            controls=[
                                ft.Text(task.get("title", "Untitled Task"), weight=ft.FontWeight.BOLD),
                                ft.Text(f"Due: {due_text}"),
                                ft.Text(f"Type: {task.get('task_type', '-')}, Priority: {task.get('priority', '-')}"),
                            ]
                        ),
                    )
                )
            )
    else:
        task_controls.append(ft.Text("No tasks due today or tomorrow."))

    upcoming_events = []
    for event in events:
        start = event.get("starts_at")
        if hasattr(start, "replace") and start >= now:
            upcoming_events.append(event)
    upcoming_events.sort(key=lambda row: row.get("starts_at"))
    upcoming_events = upcoming_events[:3]

    event_controls = []
    if upcoming_events:
        for event in upcoming_events:
            start = event.get("starts_at")
            end = event.get("ends_at")
            start_text = start.strftime("%Y-%m-%d %H:%M") if hasattr(start, "strftime") else "-"
            end_text = end.strftime("%Y-%m-%d %H:%M") if hasattr(end, "strftime") else "-"
            event_controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=10,
                        content=ft.Column(
                            controls=[
                                ft.Text(event.get("title", "Untitled Event"), weight=ft.FontWeight.BOLD),
                                ft.Text(f"Type: {event.get('event_type', '-')}") ,
                                ft.Text(f"{start_text} → {end_text}"),
                            ]
                        ),
                    )
                )
            )
    else:
        event_controls.append(ft.Text("No upcoming events."))

    return ft.View(
        route="/dashboard",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Today")),
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        offline_banner,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column([
                                    ft.Text("Today Dashboard", size=26, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Current date/time: {now.strftime('%Y-%m-%d %H:%M')}"),
                                ]),
                                term_dropdown,
                            ]
                        ),
                        ft.Row(
                            wrap=True,
                            controls=[
                                ft.ElevatedButton("Manage Subjects", on_click=lambda _: on_manage_subjects()),
                                ft.ElevatedButton("Manage Tasks", on_click=lambda _: on_manage_tasks()),
                                ft.ElevatedButton("Open Calendar", on_click=lambda _: on_manage_calendar()),
                                ft.ElevatedButton("Grades", on_click=lambda _: on_manage_grades()),
                                ft.OutlinedButton("Refresh", on_click=lambda _: page.go("/dashboard")),
                                ft.TextButton("Logout", on_click=lambda _: on_logout()),
                            ],
                        ),
                        ft.Text(
                            f"SGPA: {sgpa_value:.2f}" if isinstance(sgpa_value, (int, float)) else "SGPA: -"
                        ),
                        ft.Text(
                            f"CGPA: {cgpa_value:.2f}" if isinstance(cgpa_value, (int, float)) else "CGPA: -"
                        ),
                        ft.Divider(),
                        ft.Text(
                            f"Class timetable for {target_day_date.strftime('%Y-%m-%d')} ({target_day_name})",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        ),
                        *class_controls,
                        ft.Divider(),
                        ft.Text("Tasks due today or tomorrow", size=20, weight=ft.FontWeight.BOLD),
                        *task_controls,
                        ft.Divider(),
                        ft.Text("Next upcoming events", size=20, weight=ft.FontWeight.BOLD),
                        *event_controls,
                    ],
                ),
            ),
        ],
    )
