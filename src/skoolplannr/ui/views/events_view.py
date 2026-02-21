import calendar
from datetime import datetime, timedelta
from typing import Callable, Optional
import flet as ft

from skoolplannr.services.firestore_service import FirestoreService
from skoolplannr.state.app_state import AppState


DATE_TIME_FMT = "%Y-%m-%d %H:%M"


def build_events_view(page: ft.Page, app_state: AppState, on_back: Callable[[], None]) -> ft.View:
    fs = FirestoreService.from_settings()

    title = ft.TextField(label="Event Title", width=350)
    event_type = ft.Dropdown(
        width=220,
        label="Event Type",
        value="class",
        options=[
            ft.dropdown.Option("class"),
            ft.dropdown.Option("exam"),
            ft.dropdown.Option("holiday"),
            ft.dropdown.Option("deadline"),
        ],
    )
    starts_at = ft.TextField(label="Starts (YYYY-MM-DD HH:MM)", width=240)
    ends_at = ft.TextField(label="Ends (YYYY-MM-DD HH:MM)", width=240)
    subject = ft.Dropdown(width=320, label="Subject (optional)")
    status = ft.Text(color=ft.Colors.RED_400)
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Upcoming"),
            ft.Tab(text="Week"),
            ft.Tab(text="Month"),
        ],
        on_change=lambda _: refresh_events(),
    )
    calendar_container = ft.Container()

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

    def refresh_events() -> None:
        uid = app_state.session.uid
        if not uid:
            set_status("No active session.")
            page.update()
            return

        calendar_container.content = ft.Column()
        events = fs.list_events(uid)

        if not events:
            calendar_container.content = ft.Text("No events added yet.")
            page.update()
            return

        def make_delete_handler(event_id: str):
            def handler(_):
                fs.delete_event(uid, event_id)
                refresh_events()
                page.update()
            return handler

        def build_list_view(events):
            col = ft.Column(spacing=8)
            for event in events:
                start = event.get("starts_at")
                end = event.get("ends_at")
                start_text = start.strftime(DATE_TIME_FMT) if hasattr(start, "strftime") else "-"
                end_text = end.strftime(DATE_TIME_FMT) if hasattr(end, "strftime") else "-"
                col.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=12,
                            content=ft.Column(
                                controls=[
                                    ft.Text(event.get("title", "Untitled Event"), weight=ft.FontWeight.BOLD),
                                    ft.Text(f"Type: {event.get('event_type', '-')}"),
                                    ft.Text(f"Starts: {start_text}"),
                                    ft.Text(f"Ends: {end_text}"),
                                    ft.Row(controls=[ft.TextButton("Delete", on_click=make_delete_handler(event["id"]))]),
                                ]
                            ),
                        )
                    )
                )
            return col

        def build_week_view(events):
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_week = start_of_week + timedelta(days=7)

            week_events = []
            for e in events:
                start = e.get("starts_at")
                if hasattr(start, "date"):
                    if start_of_week.date() <= start.date() < end_of_week.date():
                        week_events.append(e)

            days_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            for i in range(7):
                day_date = start_of_week + timedelta(days=i)
                day_events = [e for e in week_events if e.get("starts_at").date() == day_date.date()]

                day_col = ft.Column(expand=1)
                is_today = day_date.date() == today.date()
                day_col.controls.append(
                    ft.Container(
                        content=ft.Text(day_date.strftime("%a %b %d"), weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                        bgcolor=ft.Colors.BLUE_GREY_50 if not is_today else ft.Colors.BLUE_100,
                        padding=5,
                        border_radius=5,
                        alignment=ft.alignment.center
                    )
                )

                for ev in day_events:
                    start_val = ev.get('starts_at')
                    time_str = start_val.strftime('%H:%M') if hasattr(start_val, "strftime") else ""
                    day_col.controls.append(
                        ft.Container(
                            content=ft.Text(f"{time_str} {ev.get('title')}", size=12),
                            bgcolor=ft.Colors.BLUE_50,
                            padding=5,
                            border_radius=5
                        )
                    )
                days_row.controls.append(
                    ft.Container(content=day_col, expand=1, border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT), padding=4, border_radius=4)
                )

            return ft.Container(content=days_row, border=ft.border.all(1, ft.Colors.OUTLINE), border_radius=5, padding=10)

        def build_month_view(events):
            today = datetime.now()
            year = today.year
            month = today.month

            cal = calendar.monthcalendar(year, month)
            month_col = ft.Column(spacing=0)

            header_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                header_row.controls.append(
                    ft.Container(content=ft.Text(day_name, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER), expand=1, alignment=ft.alignment.center)
                )
            month_col.controls.append(header_row)

            for week in cal:
                week_row = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                for day in week:
                    if day == 0:
                        week_row.controls.append(ft.Container(expand=1))
                    else:
                        day_date = datetime(year, month, day).date()
                        day_events = [e for e in events if hasattr(e.get("starts_at"), "date") and e.get("starts_at").date() == day_date]

                        day_content = ft.Column(spacing=2)
                        is_today = day_date == today.date()
                        day_content.controls.append(ft.Text(str(day), weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL))

                        for ev in day_events[:3]:
                            start_val = ev.get('starts_at')
                            time_str = start_val.strftime('%H:%M') if hasattr(start_val, "strftime") else ""
                            day_content.controls.append(
                                ft.Container(
                                    content=ft.Text(f"{time_str} {ev.get('title')}", size=10, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                                    bgcolor=ft.Colors.BLUE_50,
                                    padding=2,
                                    border_radius=2,
                                    tooltip=f"{time_str} {ev.get('title')}"
                                )
                            )
                        if len(day_events) > 3:
                            day_content.controls.append(ft.Text(f"+{len(day_events)-3} more", size=10, color=ft.Colors.GREY))

                        week_row.controls.append(
                            ft.Container(
                                content=day_content,
                                expand=1,
                                height=100,
                                border=ft.border.all(1, ft.Colors.OUTLINE_VARIANT),
                                padding=4,
                                bgcolor=ft.Colors.BLUE_50 if is_today else None
                            )
                        )
                month_col.controls.append(week_row)

            return ft.Container(
                content=ft.Column([
                    ft.Text(f"{calendar.month_name[month]} {year}", size=18, weight=ft.FontWeight.BOLD),
                    month_col
                ]),
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
                padding=10
            )

        selected_view = tabs.selected_index
        if selected_view == 0:
            calendar_container.content = build_list_view(events)
        elif selected_view == 1:
            calendar_container.content = build_week_view(events)
        elif selected_view == 2:
            calendar_container.content = build_month_view(events)

        page.update()

    def on_add(_):
        uid = app_state.session.uid
        if not uid:
            set_status("No active session.")
            page.update()
            return

        if not title.value or not starts_at.value or not ends_at.value:
            set_status("Title, start, and end time are required.")
            page.update()
            return

        try:
            parsed_start = datetime.strptime(starts_at.value.strip(), DATE_TIME_FMT)
            parsed_end = datetime.strptime(ends_at.value.strip(), DATE_TIME_FMT)
        except ValueError:
            set_status("Invalid date/time format. Use YYYY-MM-DD HH:MM.")
            page.update()
            return

        if parsed_end < parsed_start:
            set_status("End time must be after start time.")
            page.update()
            return

        try:
            fs.create_event(
                uid,
                title=title.value.strip(),
                event_type=event_type.value or "class",
                starts_at=parsed_start,
                ends_at=parsed_end,
                subject_id=_subject_id(),
            )
            title.value = ""
            starts_at.value = ""
            ends_at.value = ""
            subject.value = ""
            set_status("Event added.", is_error=False)
            refresh_events()
        except Exception as exc:
            set_status(f"Failed to add event: {exc}")
            page.update()

    refresh_subject_options()
    refresh_events()

    return ft.View(
        route="/calendar",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Calendar")),
            ft.Container(
                padding=20,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    controls=[
                        ft.Row(controls=[ft.ElevatedButton("Back to Dashboard", on_click=lambda _: on_back())]),
                        ft.Text("Add Event", size=22, weight=ft.FontWeight.BOLD),
                        title,
                        ft.Row(controls=[event_type, subject]),
                        ft.Row(controls=[starts_at, ends_at]),
                        ft.ElevatedButton("Add Event", on_click=on_add),
                        status,
                        ft.Divider(),
                        ft.Text("Calendar", size=20, weight=ft.FontWeight.BOLD),
                        tabs,
                        calendar_container,
                    ],
                ),
            ),
        ],
    )
