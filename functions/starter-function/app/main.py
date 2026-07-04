import os

import flet as ft

from app.ui.app import main


if __name__ == "__main__":
    web_mode = os.getenv("ACADEMASYNC_WEB", "0") == "1"
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER if web_mode else ft.AppView.FLET_APP,
        port=int(os.getenv("PORT", "8550")),
    )
