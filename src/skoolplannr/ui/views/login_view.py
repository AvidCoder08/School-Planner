from typing import Callable
import flet as ft

from skoolplannr.services.auth_service import FirebaseAuthService, AuthServiceError
from skoolplannr.services.firestore_service import FirestoreService, FirestoreServiceError
from skoolplannr.state.app_state import AppState


def build_login_view(
    page: ft.Page,
    app_state: AppState,
    on_authenticated: Callable[[], None],
) -> ft.View:
    email = ft.TextField(label="Email", width=350)
    password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=350)
    status_text = ft.Text(color=ft.Colors.RED_400)

    def set_status(message: str, is_error: bool = True) -> None:
        status_text.value = message
        status_text.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400
        page.update()

    def complete_login(auth_result) -> None:
        app_state.session.uid = auth_result.uid
        app_state.session.email = auth_result.email
        app_state.session.id_token = auth_result.id_token
        app_state.session.refresh_token = auth_result.refresh_token

        try:
            fs = FirestoreService.from_settings()
            fs.ensure_user_profile(auth_result.uid, auth_result.email)
        except FirestoreServiceError as exc:
            set_status(f"Firestore config error: {exc}")
            return
        except Exception as exc:
            set_status(f"Could not initialize profile: {exc}")
            return

        on_authenticated()

    def on_sign_in(_):
        if not email.value or not password.value:
            set_status("Email and password are required.")
            return

        try:
            auth = FirebaseAuthService.from_settings()
            result = auth.sign_in(email.value.strip(), password.value)
            complete_login(result)
        except AuthServiceError as exc:
            set_status(f"Sign in failed: {exc}")
        except Exception as exc:
            set_status(f"Unexpected error: {exc}")

    def on_sign_up(_):
        if not email.value or not password.value:
            set_status("Email and password are required.")
            return
        if len(password.value) < 6:
            set_status("Password must be at least 6 characters.")
            return

        try:
            auth = FirebaseAuthService.from_settings()
            result = auth.sign_up(email.value.strip(), password.value)
            complete_login(result)
        except AuthServiceError as exc:
            set_status(f"Sign up failed: {exc}")
        except Exception as exc:
            set_status(f"Unexpected error: {exc}")

    return ft.View(
        route="/login",
        controls=[
            ft.AppBar(title=ft.Text("SkoolPlannr - Login")),
            ft.Container(
                alignment=ft.Alignment.CENTER,
                padding=20,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text("Welcome to SkoolPlannr", size=30, weight=ft.FontWeight.BOLD),
                        ft.Text("Sign in or create an account to continue."),
                        email,
                        password,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[
                                ft.Button("Sign In", on_click=on_sign_in),
                                ft.OutlinedButton("Sign Up", on_click=on_sign_up),
                            ],
                        ),
                        status_text,
                    ],
                ),
            ),
        ],
    )
