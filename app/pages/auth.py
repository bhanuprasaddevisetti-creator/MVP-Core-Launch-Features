import reflex as rx

from app import design
from app.states.auth_state import AuthState
from app.states.language_state import LanguageState

_GRID = (
    "grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 md:p-6 min-h-screen "
    "lg:auto-rows-[minmax(3rem,auto)]"
)


def _hero() -> rx.Component:
    return rx.el.section(
        rx.image(
            src="/documentary_editorial_telangana.png",
            class_name="h-full min-h-[28rem] w-full object-cover",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("languages", class_name="h-4 w-4"),
                LanguageState.switch_label,
                on_click=LanguageState.toggle_language,
                class_name=(
                    "absolute right-5 top-5 inline-flex items-center gap-2 "
                    "rounded-xl bg-white/90 px-3 py-1.5 text-sm "
                    "font-semibold text-[#123524]"
                ),
            ),
            rx.el.h1(
                "Field-to-market welcome",
                class_name="text-3xl font-semibold tracking-tight",
            ),
            rx.el.p(
                "\u0c2a\u0c02\u0c1f \u0c28\u0c41\u0c02\u0c1a\u0c3f "
                "\u0c2e\u0c40 \u0c07\u0c02\u0c1f\u0c3f \u0c35\u0c30\u0c15\u0c41",
                class_name=design.TELUGU_TEXT + " text-lg text-[#FCEFCF]",
            ),
            rx.el.p(
                "Fresh Telangana harvests with distance, harvest date and "
                "mandi context shown up front \u2014 nothing hidden.",
                class_name="max-w-md text-base font-medium text-white/90",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("shopping-basket", class_name="h-4 w-4"),
                    rx.el.span(
                        "Customers buy nearest-first from verified farms",
                        class_name="text-sm font-semibold",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.div(
                    rx.icon("tractor", class_name="h-4 w-4"),
                    rx.el.span(
                        "Farmers list harvests with same-day photo proof",
                        class_name="text-sm font-semibold",
                    ),
                    class_name="flex items-center gap-2",
                ),
                class_name="space-y-1.5 rounded-xl bg-[#123524]/60 p-3",
            ),
            class_name=(
                "absolute inset-0 flex flex-col justify-end gap-3 "
                "bg-gradient-to-t from-[#123524]/90 via-[#123524]/40 "
                "to-transparent p-8 text-white"
            ),
        ),
        id="auth-hero",
        class_name=(
            "relative col-span-12 lg:col-start-1 lg:col-span-7 lg:row-start-1 "
            "lg:row-span-10 overflow-hidden rounded-xl"
        ),
    )


def _form() -> rx.Component:
    return rx.el.form(
        rx.el.h1("Login and signup", class_name=design.HEADING_LG),
        rx.el.p(
            rx.cond(
                AuthState.mode == "login",
                "Sign in to continue where you left off.",
                "Create your account as a customer or a farmer.",
            ),
            class_name=design.HELPER,
        ),
        rx.cond(
            AuthState.mode == "signup",
            rx.el.div(
                rx.el.label("Full name", class_name=design.LABEL),
                rx.el.input(
                    name="full_name",
                    placeholder="Your name",
                    default_value=AuthState.full_name,
                    class_name=design.INPUT,
                ),
                class_name="space-y-1",
            ),
            rx.fragment(),
        ),
        rx.el.div(
            rx.el.label("Email", class_name=design.LABEL),
            rx.el.input(
                name="email",
                type="email",
                placeholder="you@example.com",
                default_value=AuthState.email,
                class_name=design.INPUT,
            ),
            class_name="space-y-1",
        ),
        rx.el.div(
            rx.el.label("Password", class_name=design.LABEL),
            rx.el.input(
                name="password",
                type="password",
                placeholder="At least 8 characters",
                class_name=design.INPUT,
            ),
            class_name="space-y-1",
        ),
        rx.cond(
            AuthState.mode == "signup",
            rx.el.div(
                rx.el.label("I am joining as", class_name=design.LABEL),
                rx.el.select(
                    rx.el.option(
                        "Customer \u00b7 buying produce", value="customer"
                    ),
                    rx.el.option(
                        "Farmer \u00b7 selling produce", value="farmer"
                    ),
                    name="role",
                    default_value=AuthState.selected_role,
                    class_name=design.INPUT + " appearance-none",
                ),
                class_name="space-y-1",
            ),
            rx.fragment(),
        ),
        rx.el.button(
            rx.cond(AuthState.mode == "login", "Sign in", "Create account"),
            type="submit",
            disabled=AuthState.loading,
            class_name=design.BUTTON_PRIMARY + " w-full",
        ),
        rx.el.button(
            rx.cond(
                AuthState.mode == "login",
                "Need an account? Sign up",
                "Already registered? Sign in",
            ),
            type="button",
            on_click=AuthState.toggle_mode,
            class_name=design.BUTTON_SECONDARY + " w-full",
        ),
        rx.cond(
            AuthState.error != "",
            rx.el.p(
                AuthState.error, class_name="text-sm font-medium text-red-600"
            ),
            rx.fragment(),
        ),
        rx.cond(
            AuthState.message != "",
            rx.el.p(
                AuthState.message,
                class_name="text-sm font-semibold text-[#1B5E3A]",
            ),
            rx.fragment(),
        ),
        rx.el.p(
            "Forgot your password? Ask the marketplace team to reset it from "
            "the admin panel \u2014 self-service recovery arrives with "
            "notifications.",
            class_name=design.HELPER,
        ),
        on_submit=AuthState.submit_form,
        id="auth-form",
        class_name=(
            "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-1 "
            "lg:row-span-10 space-y-4 self-start rounded-xl border "
            "border-[#E7DCC8] bg-white p-8"
        ),
    )


def login_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(_hero(), _form(), class_name=_GRID),
        class_name=design.APP_SHELL,
    )
