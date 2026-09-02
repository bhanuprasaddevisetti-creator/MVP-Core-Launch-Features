import reflex as rx

from app import design
from app.states.auth_state import AuthState


def admin_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.el.h1("Admin control room", class_name=design.HEADING_MD),
                rx.el.button(
                    "Log out",
                    on_click=AuthState.logout,
                    class_name=design.BUTTON_SECONDARY,
                ),
                class_name="flex items-center justify-between",
            ),
            rx.el.p(
                "Signed in as admin. Add farmer verification, listing "
                "moderation, and payout tools here next.",
                class_name=design.HELPER,
            ),
            class_name="mx-auto max-w-4xl space-y-4 p-6",
        ),
        class_name=design.APP_SHELL,
    )
