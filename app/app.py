import reflex as rx
from app.pages.admin import admin_page
from app.states.auth_state import AuthState

from app import design
from app.pages.advisory import advisory_page
from app.pages.auth import login_page
from app.pages.farmer_studio import farmer_studio_page
from app.pages.listing_detail import listing_detail_page
from app.pages.marketplace import marketplace
from app.states.advisory_state import AdvisoryState
from app.states.farmer_studio_state import FarmerStudioState
from app.states.listing_state import ListingState
from app.states.marketplace_state import MarketplaceState

# Database seeding is managed outside application import time.


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.icon("sprout", class_name="h-5 w-5"),
                rx.el.span("Rythu Mithra"),
                class_name=(
                    "w-fit inline-flex items-center gap-2 rounded-full "
                    "bg-[#DCEBE0] px-3 py-1 text-sm font-semibold "
                    "text-[#1B5E3A]"
                ),
            ),
            rx.el.h1(
                "Fresh Telangana harvests, nearest first",
                class_name=(
                    "mt-6 text-3xl font-semibold tracking-tight text-[#123524]"
                ),
            ),
            rx.el.p(
                "\u0c2e\u0c3e\u0c30\u0c4d\u0c15\u0c46\u0c1f\u0c4d "
                "\u0c2a\u0c4d\u0c30\u0c3e\u0c30\u0c02\u0c2d\u0c02 "
                "\u0c38\u0c3f\u0c26\u0c4d\u0c27\u0c02",
                class_name=(
                    "mt-2 text-lg font-medium text-[#4A3F35] "
                    "font-['Noto_Sans_Telugu']"
                ),
            ),
            rx.el.div(
                rx.el.a(
                    "Browse harvests",
                    href="/marketplace",
                    class_name=design.BUTTON_PRIMARY,
                ),
                rx.el.a(
                    "Sell your produce",
                    href="/farmer/listings",
                    class_name=design.BUTTON_SECONDARY,
                ),
                class_name="mt-6 flex flex-wrap items-center justify-center gap-3",
            ),
            class_name=(
                "mx-auto flex min-h-screen max-w-2xl flex-col items-center "
                "justify-center px-6 text-center"
            ),
        ),
        class_name=design.APP_SHELL,
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(href=design.FONT_LINKS_HREF, rel="stylesheet"),
    ],
)
app.add_page(
    admin_page,
    route="/admin",
    on_load=OtpAuthState.guard_admin,
)
app.add_page(index, route="/")
app.add_page(login_page, route="/login")
app.add_page(
    marketplace,
    route="/marketplace",
    on_load=MarketplaceState.load_listings,
)
app.add_page(
    farmer_studio_page,
    route="/farmer/listings",
    on_load=FarmerStudioState.guard,
)
app.add_page(
    advisory_page, route="/advisory", on_load=AdvisoryState.load_articles
)
