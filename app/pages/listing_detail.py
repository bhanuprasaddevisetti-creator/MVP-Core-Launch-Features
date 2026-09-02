import reflex as rx

from app import design
from app.components.nav import site_nav
from app.states.language_state import LanguageState
from app.states.listing_state import AdviceTip, ListingState

_GRID = (
    "grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 md:p-6 "
    "lg:auto-rows-[minmax(3.5rem,auto)]"
)


def _fact(label: str, value: rx.Component | str) -> rx.Component:
    return rx.el.div(
        rx.el.dt(label, class_name=design.HELPER),
        rx.el.dd(value, class_name="text-base font-semibold text-[#123524]"),
        class_name="space-y-1",
    )


def _tip(tip: AdviceTip) -> rx.Component:
    return rx.el.article(
        rx.el.h4(
            rx.cond(LanguageState.is_telugu, tip["title_te"], tip["title"]),
            class_name="text-sm font-semibold text-[#123524]",
        ),
        rx.el.p(tip["summary"], class_name=design.HELPER),
        rx.el.a(
            f"Read source \u00b7 {tip['source']}",
            href=tip["url"],
            target="_blank",
            class_name="text-xs font-semibold text-[#1B5E3A] underline",
        ),
        class_name="space-y-1 rounded-xl bg-[#F6EFE2] p-3",
    )


def _proof_gallery() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.image(
                src=ListingState.listing["image"].to(str),
                class_name="h-full w-full object-cover",
            ),
            rx.el.div(
                rx.el.p(
                    "Same-day crop photo proof",
                    class_name="text-lg font-semibold text-white",
                ),
                rx.el.div(
                    rx.cond(
                        ListingState.listing["same_day"],
                        rx.el.span(
                            rx.icon("camera", class_name="h-3 w-3"),
                            f"Captured {ListingState.listing['capture_date'].to(str)}",
                            class_name=design.BADGE_FRESH,
                        ),
                        rx.el.span(
                            rx.icon("clock", class_name="h-3 w-3"),
                            "Awaiting today's photo proof",
                            class_name=design.BADGE_NEUTRAL,
                        ),
                    ),
                    rx.el.span(
                        rx.icon("map-pin", class_name="h-3 w-3"),
                        ListingState.listing["distance_label"].to(str),
                        class_name=design.BADGE_DISTANCE,
                    ),
                    class_name="flex flex-wrap items-center gap-2",
                ),
                class_name=(
                    "absolute inset-x-0 bottom-0 space-y-2 "
                    "bg-gradient-to-t from-[#123524]/90 to-transparent p-5"
                ),
            ),
            class_name="relative h-full min-h-[22rem] w-full",
        ),
        id="proof-gallery",
        class_name=(
            "col-span-12 lg:col-start-1 lg:col-span-7 lg:row-start-2 "
            "lg:row-span-7 overflow-hidden rounded-xl border "
            "border-[#E7DCC8] bg-[#F6EFE2]"
        ),
    )


def _crop_detail() -> rx.Component:
    return rx.el.section(
        rx.el.h1("Crop and freshness details", class_name=design.HEADING_MD),
        rx.el.h2(
            rx.cond(
                LanguageState.is_telugu,
                ListingState.listing["crop_te"].to(str),
                ListingState.listing["crop"].to(str),
            ),
            class_name="text-2xl font-semibold tracking-tight text-[#123524]",
        ),
        rx.el.div(
            rx.el.span(
                ListingState.listing["freshness"].to(str),
                class_name=design.BADGE_FRESH,
            ),
            rx.el.span(
                ListingState.listing["distance_label"].to(str),
                class_name=design.BADGE_DISTANCE,
            ),
            rx.cond(
                ListingState.listing["verified"],
                rx.el.span(
                    rx.icon("badge-check", class_name="h-3 w-3"),
                    "Verified farmer",
                    class_name=design.BADGE_VERIFIED,
                ),
                rx.fragment(),
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.dl(
            _fact(
                "Farmer price",
                f"\u20b9{ListingState.listing['price'].to(float):.2f} / {ListingState.listing['unit'].to(str)}",
            ),
            _fact(
                "Local mandi average",
                f"\u20b9{ListingState.listing['mandi_price'].to(float):.2f} \u00b7 {ListingState.listing['mandi_name'].to(str)}",
            ),
            _fact(
                "Available quantity",
                f"{ListingState.listing['quantity'].to(float):.1f} {ListingState.listing['unit'].to(str)}",
            ),
            _fact("Harvest date", ListingState.listing["harvest"].to(str)),
            _fact("Listed on", ListingState.listing["listed_label"].to(str)),
            _fact(
                "Farm location",
                f"{ListingState.listing['village'].to(str)}, {ListingState.listing['district'].to(str)}",
            ),
            class_name="grid grid-cols-2 gap-4",
        ),
        rx.el.p(
            rx.cond(
                LanguageState.is_telugu,
                ListingState.listing["description_te"].to(str),
                ListingState.listing["description"].to(str),
            ),
            class_name=design.BODY,
        ),
        id="crop-detail",
        class_name=(
            "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-2 "
            "lg:row-span-5 space-y-4 overflow-y-auto rounded-xl border "
            "border-[#E7DCC8] bg-white p-5"
        ),
    )


def _farmer_profile() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(
                "Verified farmer profile",
                class_name="text-sm font-semibold text-[#4A3F35]",
            ),
            rx.cond(
                ListingState.listing["local_partner"],
                rx.el.span("Local partner", class_name=design.BADGE_VERIFIED),
                rx.fragment(),
            ),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.el.p(
            rx.cond(
                LanguageState.is_telugu,
                ListingState.listing["farmer_te"].to(str),
                ListingState.listing["farmer"].to(str),
            ),
            class_name="text-lg font-semibold text-[#123524]",
        ),
        rx.el.p(
            rx.cond(
                LanguageState.is_telugu,
                ListingState.listing["bio_te"].to(str),
                ListingState.listing["bio"].to(str),
            ),
            class_name=design.HELPER + " line-clamp-2",
        ),
        rx.cond(
            ListingState.voice_url != "",
            rx.audio(
                url=ListingState.voice_url,
                controls=True,
                width="100%",
                height="42px",
            ),
            rx.el.p(
                "Voice introduction not recorded yet.",
                class_name=design.HELPER,
            ),
        ),
        id="farmer-profile",
        class_name=(
            "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-7 "
            "lg:row-span-2 space-y-2 rounded-xl border border-[#E7DCC8] "
            "bg-[#F6EFE2] p-4"
        ),
    )


def _order_request() -> rx.Component:
    return rx.el.form(
        rx.el.h3("Request this order", class_name=design.HEADING_MD),
        rx.el.p(
            "Prepare your request now \u2014 payment and chat open in the "
            "next release.",
            class_name=design.HELPER,
        ),
        rx.el.div(
            rx.el.div(
                rx.el.label("Quantity", class_name=design.LABEL),
                rx.el.input(
                    name="quantity",
                    type="number",
                    step="0.1",
                    placeholder="e.g. 10",
                    default_value=ListingState.draft_quantity,
                    class_name=design.INPUT,
                ),
                class_name="space-y-1",
            ),
            rx.el.div(
                rx.el.label("Fulfilment", class_name=design.LABEL),
                rx.el.select(
                    rx.el.option("Farm pickup", value="farm_pickup"),
                    rx.el.option("Local delivery", value="local_delivery"),
                    name="mode",
                    default_value=ListingState.draft_mode,
                    class_name=design.INPUT + " appearance-none",
                ),
                class_name="space-y-1",
            ),
            rx.el.div(
                rx.el.label("Note for the farmer", class_name=design.LABEL),
                rx.el.input(
                    name="note",
                    placeholder="Pickup time, packing, transport\u2026",
                    default_value=ListingState.draft_note,
                    class_name=design.INPUT,
                ),
                class_name="space-y-1 md:col-span-2",
            ),
            class_name="grid grid-cols-1 gap-3 md:grid-cols-2",
        ),
        rx.el.div(
            rx.el.p(
                f"Estimated total \u20b9{ListingState.draft_total:.2f}",
                class_name="text-lg font-semibold text-[#1B5E3A]",
            ),
            rx.el.button(
                rx.icon("clipboard-check", class_name="h-4 w-4"),
                "Validate request draft",
                type="submit",
                class_name=design.BUTTON_PRIMARY,
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.cond(
            ListingState.draft_error != "",
            rx.el.p(
                ListingState.draft_error,
                class_name="text-sm font-medium text-red-600",
            ),
            rx.cond(
                ListingState.draft_ready,
                rx.el.p(
                    "Draft looks good. It will be sent to the farmer once the "
                    "order workflow goes live.",
                    class_name="text-sm font-semibold text-[#1B5E3A]",
                ),
                rx.fragment(),
            ),
        ),
        on_submit=ListingState.prepare_draft,
        id="order-request",
        class_name=(
            "col-span-12 lg:col-start-1 lg:col-span-7 lg:row-start-9 "
            "lg:row-span-4 space-y-4 rounded-xl border border-[#E7DCC8] "
            "bg-white p-5"
        ),
    )


def listing_detail_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            site_nav("detail-nav", "Browse"),
            _proof_gallery(),
            _crop_detail(),
            _farmer_profile(),
            _order_request(),
            rx.el.div(
                rx.el.h3("Relevant crop advice", class_name=design.HEADING_MD),
                rx.cond(
                    ListingState.tips.length() == 0,
                    rx.el.p(
                        "Advisory notes for this crop are being reviewed.",
                        class_name=design.HELPER,
                    ),
                    rx.el.div(
                        rx.foreach(ListingState.tips, _tip),
                        class_name="space-y-2",
                    ),
                ),
                rx.el.a(
                    "Open advisory library",
                    href="/advisory",
                    class_name=design.BUTTON_SECONDARY,
                ),
                id="detail-advice",
                class_name=(
                    "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-9 "
                    "lg:row-span-4 space-y-3 overflow-y-auto rounded-xl "
                    "border border-[#E7DCC8] bg-white p-5"
                ),
            ),
            class_name=_GRID,
        ),
        rx.cond(
            ListingState.error != "",
            rx.el.p(
                ListingState.error,
                class_name="px-6 pb-6 text-sm font-medium text-red-600",
            ),
            rx.fragment(),
        ),
        class_name=design.APP_SHELL,
    )
