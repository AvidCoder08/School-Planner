import sys
from pathlib import Path
import threading
import time
from datetime import datetime, timedelta, timezone

import flet as ft

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skoolplannr.services.firestore_service import FirestoreService
from skoolplannr.state.app_state import app_state
from skoolplannr.ui.views.dashboard_view import build_dashboard_view
from skoolplannr.ui.views.login_view import build_login_view
from skoolplannr.ui.views.onboarding_view import build_onboarding_view
from skoolplannr.ui.views.events_view import build_events_view
from skoolplannr.ui.views.grades_view import build_grades_view
from skoolplannr.ui.views.subjects_view import build_subjects_view
from skoolplannr.ui.views.tasks_view import build_tasks_view


def main(page: ft.Page) -> None:
    page.title = "SkoolPlannr"
    page.theme_mode = ft.ThemeMode.SYSTEM
    
    notified_ids = set()

    def notification_worker():
        while True:
            time.sleep(60)
            uid = app_state.session.uid
            if not uid:
                continue

            try:
                fs = FirestoreService.from_settings()
                tasks = fs.list_tasks(uid, include_completed=False)
                events = fs.list_events(uid)

                now = datetime.now(timezone.utc)
                warning_threshold = now + timedelta(minutes=15)

                notifications_to_show = []

                for task in tasks:
                    due = task.get("due_at")
                    if not due or task.get("id") in notified_ids:
                        continue
                    if hasattr(due, "tzinfo") and due.tzinfo is None:
                        due = due.replace(tzinfo=timezone.utc)
                    if now <= due <= warning_threshold:
                        notifications_to_show.append(f"Task Due Soon: {task.get('title')}")
                        notified_ids.add(task.get("id"))

                for event in events:
                    start = event.get("starts_at")
                    if not start or event.get("id") in notified_ids:
                        continue
                    if hasattr(start, "tzinfo") and start.tzinfo is None:
                        start = start.replace(tzinfo=timezone.utc)
                    if now <= start <= warning_threshold:
                        notifications_to_show.append(f"Event Starting Soon: {event.get('title')}")
                        notified_ids.add(event.get("id"))

                for msg in notifications_to_show:
                    snack = ft.SnackBar(ft.Text(msg, weight=ft.FontWeight.BOLD), bgcolor=ft.Colors.BLUE_800)
                    page.snack_bar = snack
                    snack.open = True
                    page.update()
                    time.sleep(2) # Stagger multiple notifications

            except Exception as e:
                # Silently ignore errors in polling thread (e.g. offline)
                pass

    bg_thread = threading.Thread(target=notification_worker, daemon=True)
    bg_thread.start()

    def has_completed_onboarding() -> bool:
        if not app_state.session.uid:
            return False
        fs = FirestoreService.from_settings()
        return fs.has_onboarding(app_state.session.uid)

    def route_guard() -> str:
        if not app_state.session.is_authenticated:
            return "/login"
        if has_completed_onboarding():
            return "/dashboard"
        return "/onboarding"

    async def _push_route(route: str) -> None:
        await page.push_route(route)

    def navigate(route: str) -> None:
        page.run_task(_push_route, route)

    def go_guarded() -> None:
        navigate(route_guard())

    def logout() -> None:
        app_state.session.clear()
        navigate("/login")

    def route_change(_: ft.RouteChangeEvent) -> None:
        page.views.clear()

        if page.route == "/login":
            page.views.append(
                build_login_view(
                    page=page,
                    app_state=app_state,
                    on_authenticated=go_guarded,
                )
            )
        elif page.route == "/onboarding":
            if not app_state.session.is_authenticated:
                navigate("/login")
                return
            page.views.append(
                build_onboarding_view(
                    page=page,
                    app_state=app_state,
                    on_complete=go_guarded,
                )
            )
        elif page.route == "/dashboard":
            if not app_state.session.is_authenticated:
                navigate("/login")
                return
            page.views.append(
                build_dashboard_view(
                    page=page,
                    app_state=app_state,
                    on_manage_subjects=lambda: navigate("/subjects"),
                    on_manage_tasks=lambda: navigate("/tasks"),
                    on_manage_calendar=lambda: navigate("/calendar"),
                    on_manage_grades=lambda: navigate("/grades"),
                    on_logout=logout,
                )
            )
        elif page.route == "/subjects":
            if not app_state.session.is_authenticated:
                navigate("/login")
                return
            page.views.append(
                build_subjects_view(
                    page=page,
                    app_state=app_state,
                    on_back=lambda: navigate("/dashboard"),
                )
            )
        elif page.route == "/tasks":
            if not app_state.session.is_authenticated:
                navigate("/login")
                return
            page.views.append(
                build_tasks_view(
                    page=page,
                    app_state=app_state,
                    on_back=lambda: navigate("/dashboard"),
                )
            )
        elif page.route == "/calendar":
            if not app_state.session.is_authenticated:
                navigate("/login")
                return
            page.views.append(
                build_events_view(
                    page=page,
                    app_state=app_state,
                    on_back=lambda: navigate("/dashboard"),
                )
            )
        elif page.route == "/grades":
            if not app_state.session.is_authenticated:
                navigate("/login")
                return
            page.views.append(
                build_grades_view(
                    page=page,
                    app_state=app_state,
                )
            )
        else:
            navigate(route_guard())
            return

        page.update()

    def on_resize(_) -> None:
        """Re-render the current view when the window is resized so the
        navigation layout can toggle between rail and bottom bar."""
        route_change(ft.RouteChangeEvent(route=page.route))

    page.on_route_change = route_change
    page.on_resize = on_resize
    navigate(route_guard())


if __name__ == "__main__":
    ft.run(main)
