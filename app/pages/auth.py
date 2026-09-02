import reflex as rx

from app import design
from app.states.auth_state import AuthState


def _identifier_step() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Sign in", class_name=design.HEADING_MD),
        rx.el.p(
            "Enter your email or mobile number. We'll send a one-time code.",
            class_name=design.HELPER,
        ),
        rx.el.input(
            placeholder="you@example.com or 9876543210",
            value=AuthState.identifier,
            on_change=AuthState.set_identifier,
            class_name=design.INPUT,
        ),
        rx.cond(
            AuthState.error != "",
            rx.el.p(AuthState.error, class_name="text-sm font-medium text-red-600"),
            rx.fragment(),
        ),
        rx.el.button(
            "Send code",
            on_click=AuthState.request_otp,
            class_name=design.BUTTON_PRIMARY + " w-full",
        ),
        class_name="space-y-3",
    )


def _otp_step() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Enter your code", class_name=design.HEADING_MD),
        rx.el.p(
            f"We sent a code to {AuthState.identifier}.", class_name=design.HELPER
        ),
        rx.el.input(
            placeholder="6-digit code",
            value=AuthState.otp_input,
            on_change=AuthState.set_otp_input,
            class_name=design.INPUT,
        ),
        rx.cond(
            AuthState.error != "",
            rx.el.p(AuthState.error, class_name="text-sm font-medium text-red-600"),
            rx.fragment(),
        ),
        rx.el.button(
            "Verify and sign in",
            on_click=AuthState.verify_otp,
            class_name=design.BUTTON_PRIMARY + " w-full",
        ),
        rx.el.button(
            "Use a different email/number",
            on_click=AuthState.go_back,
            class_name=design.BUTTON_SECONDARY + " w-full",
        ),
        class_name="space-y-3",
    )


def login_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.cond(AuthState.step == "otp", _otp_step(), _identifier_step()),
            class_name="mx-auto max-w-md space-y-4 p-6",
        ),
        class_name=design.APP_SHELL,
    )
