import reflex as rx

from app import design
from app.states.otp_auth_state import OtpAuthState


def _identifier_step() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Sign in", class_name=design.HEADING_MD),
        rx.el.p(
            "Enter your email or mobile number. We'll send a one-time code.",
            class_name=design.HELPER,
        ),
        rx.el.input(
            placeholder="you@example.com or 9876543210",
            value=OtpAuthState.identifier,
            on_change=OtpAuthState.set_identifier,
            class_name=design.INPUT,
        ),
        rx.cond(
            OtpAuthState.error != "",
            rx.el.p(OtpAuthState.error, class_name="text-sm font-medium text-red-600"),
            rx.fragment(),
        ),
        rx.el.button(
            "Send code",
            on_click=OtpAuthState.request_otp,
            class_name=design.BUTTON_PRIMARY + " w-full",
        ),
        class_name="space-y-3",
    )


def _otp_step() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Enter your code", class_name=design.HEADING_MD),
        rx.el.p(
            f"We sent a code to {OtpAuthState.identifier}.", class_name=design.HELPER
        ),
        rx.el.input(
            placeholder="6-digit code",
            value=OtpAuthState.otp_input,
            on_change=OtpAuthState.set_otp_input,
            class_name=design.INPUT,
        ),
        rx.cond(
            OtpAuthState.error != "",
            rx.el.p(OtpAuthState.error, class_name="text-sm font-medium text-red-600"),
            rx.fragment(),
        ),
        rx.el.button(
            "Verify and sign in",
            on_click=OtpAuthState.verify_otp,
            class_name=design.BUTTON_PRIMARY + " w-full",
        ),
        rx.el.button(
            "Use a different email/number",
            on_click=OtpAuthState.go_back,
            class_name=design.BUTTON_SECONDARY + " w-full",
        ),
        class_name="space-y-3",
    )


def login_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.cond(OtpAuthState.step == "otp", _otp_step(), _identifier_step()),
            class_name="mx-auto max-w-md space-y-4 p-6",
        ),
        class_name=design.APP_SHELL,
    )
