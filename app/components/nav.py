import reflex as rx

from app import design
from app.states.auth_state import AuthState
from app.states.language_state import LanguageState

_ITEMS: list[tuple[str, str]] = [
    ("Browse", "/marketplace"),
    ("Sell Produce", "/farmer/listings"),
    ("Advisory", "/advisory"),
]

_PLACEMENT = (
    "col-span-12 lg:col-start-1 lg:col-span-12 lg:row-start-1 lg:row-span-1"
)


_ACTIVE_LINK = (
    "rounded-full bg-[#1B5E3A] px-3 py-1.5 text-sm font-semibold text-white"
)
_IDLE_LINK = (
    "rounded-full px-3 py-1.5 text-sm font-semibold text-[#123524] "
    "transition-colors hover:bg-[#DCEBE0]"
)


def _link_class(label: str, active: str) -> str:
    return _ACTIVE_LINK if label == active else _IDLE_LINK


def _link(item: tuple[str, str], active: str) -> rx.Component:
    return rx.el.a(
        item[0],
        href=item[1],
        class_name=_link_class(item[0], active),
    )


def site_nav(block_id: str, active: str = "Browse") -> rx.Component:
    """Shared bilingual navigation used as a grid block on every page."""
    return rx.el.nav(
        rx.el.a(
            rx.icon("sprout", class_name="h-5 w-5 text-[#1B5E3A]"),
            rx.el.span(
                "Rythu Mithra",
                class_name="text-sm font-bold tracking-tight text-[#123524]",
            ),
            href="/marketplace",
            class_name="flex items-center gap-2",
        ),
        rx.el.div(
            _link(_ITEMS[0], active),
            _link(_ITEMS[1], active),
            _link(_ITEMS[2], active),
            class_name="hidden items-center gap-1 md:flex",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("languages", class_name="h-4 w-4"),
                LanguageState.switch_label,
                on_click=LanguageState.toggle_language,
                class_name=design.BUTTON_SECONDARY + " py-1.5",
            ),
            rx.cond(
                AuthState.user_id > 0,
                rx.el.div(
                    rx.el.span(
                        AuthState.role,
                        class_name=design.BADGE_NEUTRAL + " capitalize",
                    ),
                    rx.el.button(
                        "Sign out",
                        on_click=AuthState.logout,
                        class_name=design.BUTTON_SECONDARY + " py-1.5",
                    ),
                    class_name="flex items-center gap-2",
                ),
                rx.el.a(
                    "Sign in",
                    href="/login",
                    class_name=design.BUTTON_PRIMARY + " py-1.5",
                ),
            ),
            class_name="flex items-center gap-2",
        ),
        id=block_id,
        class_name=(
            f"{_PLACEMENT} flex flex-wrap items-center justify-between gap-3 "
            "rounded-xl border border-[#E7DCC8] bg-white px-4 py-2.5"
        ),
    )
