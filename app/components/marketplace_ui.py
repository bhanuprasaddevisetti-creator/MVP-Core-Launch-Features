import reflex as rx


from app import design
from app.components.nav import site_nav
from app.states.language_state import LanguageState
from app.states.marketplace_state import ListingCard, MarketplaceState

_GRID = (
    "grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 md:p-6 "
    "lg:auto-rows-[minmax(3.25rem,auto)]"
)


def listing_card(item: ListingCard) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.image(src=item["image"], class_name="h-40 w-full object-cover"),
            rx.el.div(
                rx.el.span(
                    rx.icon("map-pin", class_name="h-3 w-3"),
                    item["distance_label"],
                    class_name=design.BADGE_DISTANCE,
                ),
                rx.el.span(item["freshness"], class_name=design.BADGE_FRESH),
                class_name="absolute left-3 top-3 flex flex-col items-start gap-1",
            ),
            rx.cond(
                item["same_day"],
                rx.el.span(
                    rx.icon("camera", class_name="h-3 w-3"),
                    "Photo today",
                    class_name=design.BADGE_VERIFIED
                    + " absolute right-3 top-3",
                ),
                rx.fragment(),
            ),
            class_name="relative",
        ),
        rx.el.div(
            rx.el.h3(
                rx.cond(LanguageState.is_telugu, item["crop_te"], item["crop"]),
                class_name="text-lg font-semibold text-[#123524]",
            ),
            rx.el.div(
                rx.el.span(
                    f"\u20b9{item['price']:.2f} / {item['unit']}",
                    class_name="text-base font-bold text-[#1B5E3A]",
                ),
                rx.el.span(
                    f"mandi \u20b9{item['mandi_price']:.2f} \u00b7 {item['mandi_delta']:.1f}%",
                    class_name=design.HELPER,
                ),
                class_name="flex flex-wrap items-baseline gap-2",
            ),
            rx.el.p(
                f"{item['quantity']:.1f} {item['unit']} available \u00b7 {item['listed_label']}",
                class_name=design.HELPER,
            ),
            rx.el.div(
                rx.el.span(
                    f"{item['farmer']} \u00b7 {item['village']}, {item['district']}",
                    class_name="text-sm font-medium text-[#4A3F35]",
                ),
                rx.cond(
                    item["verified"],
                    rx.el.span(
                        rx.icon("badge-check", class_name="h-3 w-3"),
                        "Verified",
                        class_name=design.BADGE_VERIFIED,
                    ),
                    rx.el.span(
                        "Verification pending",
                        class_name=design.BADGE_NEUTRAL,
                    ),
                ),
                class_name="flex flex-wrap items-center justify-between gap-2",
            ),
            rx.el.a(
                "View harvest",
                href=f"/listing/{item['id']}",
                class_name=design.BUTTON_PRIMARY + " w-full",
            ),
            class_name="space-y-2 p-4",
        ),
        class_name=design.SURFACE_CARD + " overflow-hidden",
    )


def _search_form() -> rx.Component:
    return rx.el.form(
        rx.el.div(
            rx.el.h1("Location and crop search", class_name=design.HEADING_MD),
            rx.el.span(
                MarketplaceState.location_status,
                class_name=design.BADGE_NEUTRAL,
            ),
            class_name="flex flex-wrap items-center justify-between gap-2",
        ),
        rx.el.div(
            rx.el.input(
                name="query",
                placeholder="Search tomato, paddy, chilli\u2026",
                default_value=MarketplaceState.query,
                class_name=design.INPUT,
            ),
            rx.el.input(
                name="district",
                placeholder="District fallback (e.g. Medak)",
                default_value=MarketplaceState.district,
                class_name=design.INPUT,
            ),
            rx.el.select(
                rx.el.option("Within 10 km", value="10"),
                rx.el.option("Within 25 km", value="25"),
                rx.el.option("Within 50 km", value="50"),
                rx.el.option("Within 100 km", value="100"),
                name="radius",
                default_value=MarketplaceState.radius_km.to_string(),
                class_name=design.INPUT + " appearance-none",
            ),
            class_name="grid grid-cols-1 gap-3 md:grid-cols-3",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("search", class_name="h-4 w-4"),
                "Find nearest harvests",
                type="submit",
                class_name=design.BUTTON_PRIMARY,
            ),
            rx.el.button(
                rx.icon("locate-fixed", class_name="h-4 w-4"),
                "Use my location",
                type="button",
                on_click=MarketplaceState.request_geolocation,
                class_name=design.BUTTON_ACCENT,
            ),
            rx.el.p(
                "Results are always sorted nearest first; the radius widens "
                "automatically when nothing is close.",
                class_name=design.HELPER,
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        on_submit=MarketplaceState.submit_search,
        id="market-search",
        class_name=(
            "col-span-12 lg:col-start-1 lg:col-span-8 lg:row-start-2 "
            "lg:row-span-2 space-y-3 rounded-xl border border-[#E7DCC8] "
            "bg-white p-5"
        ),
    )


def _filters() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Freshness and trust filters", class_name="text-base font-semibold"
        ),
        rx.el.p(
            "Harvest window, verified farmers, same-day photo proof, price "
            "ceiling and distance.",
            class_name=design.HELPER,
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("badge-check", class_name="h-3 w-3"),
                "Verified only",
                on_click=MarketplaceState.toggle_verified,
                class_name=rx.cond(
                    MarketplaceState.verified_only,
                    design.BADGE_VERIFIED + " cursor-pointer",
                    design.BADGE_NEUTRAL + " cursor-pointer",
                ),
            ),
            rx.el.button(
                rx.icon("camera", class_name="h-3 w-3"),
                "Same-day photo",
                on_click=MarketplaceState.toggle_same_day,
                class_name=rx.cond(
                    MarketplaceState.same_day_only,
                    design.BADGE_FRESH + " cursor-pointer",
                    design.BADGE_NEUTRAL + " cursor-pointer",
                ),
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option("Any harvest date", value="0"),
                rx.el.option("Harvested today", value="1"),
                rx.el.option("Last 3 days", value="3"),
                rx.el.option("Last week", value="7"),
                value=MarketplaceState.harvest_within_days.to_string(),
                on_change=MarketplaceState.set_harvest_window,
                class_name=design.INPUT + " appearance-none py-1.5",
            ),
            rx.el.select(
                rx.el.option("Any price", value="0"),
                rx.el.option("Under \u20b920", value="20"),
                rx.el.option("Under \u20b950", value="50"),
                rx.el.option("Under \u20b9100", value="100"),
                value=MarketplaceState.max_price.to_string(),
                on_change=MarketplaceState.set_max_price,
                class_name=design.INPUT + " appearance-none py-1.5",
            ),
            class_name="grid grid-cols-2 gap-2",
        ),
        id="market-filters",
        class_name=(
            "col-span-12 lg:col-start-9 lg:col-span-4 lg:row-start-2 "
            "lg:row-span-2 space-y-2 rounded-xl border border-[#E7DCC8] "
            "bg-[#F6EFE2] p-4 text-[#123524]"
        ),
    )


def _listing_grid() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2("Nearby crop listings", class_name=design.HEADING_MD),
            rx.el.span(
                MarketplaceState.result_summary,
                class_name=design.BADGE_DISTANCE,
            ),
            class_name="flex flex-wrap items-center justify-between gap-2",
        ),
        rx.cond(
            MarketplaceState.radius_notice != "",
            rx.el.p(
                MarketplaceState.radius_notice,
                class_name="text-sm font-semibold text-[#C9860B]",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MarketplaceState.loading,
            rx.el.div(
                rx.el.div(
                    class_name="h-64 animate-pulse rounded-xl bg-[#F6EFE2]"
                ),
                rx.el.div(
                    class_name="h-64 animate-pulse rounded-xl bg-[#F6EFE2]"
                ),
                class_name="grid grid-cols-1 gap-4 md:grid-cols-2",
            ),
            rx.cond(
                MarketplaceState.listings.length() == 0,
                rx.el.p(
                    "No matching harvests yet. Try another crop, a wider "
                    "radius or a nearby district.",
                    class_name=design.HELPER,
                ),
                rx.el.div(
                    rx.foreach(MarketplaceState.listings, listing_card),
                    class_name="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3",
                ),
            ),
        ),
        rx.cond(
            MarketplaceState.error != "",
            rx.el.p(
                MarketplaceState.error,
                class_name="text-sm font-medium text-red-600",
            ),
            rx.fragment(),
        ),
        id="listing-grid",
        class_name=(
            "col-span-12 lg:col-start-1 lg:col-span-8 lg:row-start-4 "
            "lg:row-span-9 space-y-4 overflow-y-auto rounded-xl border "
            "border-[#E7DCC8] bg-white p-5"
        ),
    )




def _price_spotlight() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Fair-price spotlight", class_name="text-base font-semibold"),
        rx.cond(
            MarketplaceState.listings.length() == 0,
            rx.el.p(
                "Search a crop to compare farmer offers with mandi rates.",
                class_name=design.HELPER,
            ),
            rx.el.div(
                rx.el.p(
                    MarketplaceState.spotlight["crop"].to(str),
                    class_name="font-semibold text-[#123524]",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.p("Farmer offer", class_name=design.HELPER),
                        rx.el.p(
                            f"\u20b9{MarketplaceState.spotlight['farmer_price'].to(float):.2f}",
                            class_name="text-lg font-bold text-[#1B5E3A]",
                        ),
                        class_name="flex-1",
                    ),
                    rx.el.div(
                        rx.el.p("Mandi reference", class_name=design.HELPER),
                        rx.el.p(
                            f"\u20b9{MarketplaceState.spotlight['mandi_price'].to(float):.2f}",
                            class_name="text-lg font-bold text-[#C9860B]",
                        ),
                        class_name="flex-1",
                    ),
                    class_name="flex items-end gap-3",
                ),
                rx.el.p(
                    f"{MarketplaceState.spotlight['delta'].to(float):.1f}% versus {MarketplaceState.spotlight['mandi_name'].to(str)}",
                    class_name=design.HELPER,
                ),
                class_name="space-y-1",
            ),
        ),
        id="price-spotlight",
        class_name=(
            "col-span-12 lg:col-start-9 lg:col-span-4 lg:row-start-9 "
            "lg:row-span-2 space-y-2 rounded-xl border border-[#E7DCC8] "
            "bg-[#FCEFCF] p-4"
        ),
    )


def _advisory_preview() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Seasonal advisory", class_name="text-base font-semibold"),
        rx.el.p(
            "Sourced ICAR and KVK guidance for this season\u2019s crops, "
            "reviewed for Telangana growers.",
            class_name=design.HELPER,
        ),
        rx.el.a(
            "Open advisory library",
            href="/advisory",
            class_name=design.BUTTON_SECONDARY,
        ),
        id="advisory-preview",
        class_name=(
            "col-span-12 lg:col-start-9 lg:col-span-4 lg:row-start-11 "
            "lg:row-span-2 space-y-2 rounded-xl border border-[#E7DCC8] "
            "bg-white p-4"
        ),
    )


def marketplace_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            site_nav("market-nav", "Browse"),
            _search_form(),
            _filters(),
            _listing_grid(),
            _farm_map(),
            _price_spotlight(),
            _advisory_preview(),
            class_name=_GRID,
        ),
        class_name=design.APP_SHELL,
    )
