import reflex as rx

from app import design
from app.components.nav import site_nav
from app.states.farmer_studio_state import (
    FarmerStudioState,
    FarmOption,
    MyListing,
)
from app.states.language_state import LanguageState

_GRID = (
    "grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 md:p-6 "
    "lg:auto-rows-[minmax(3.5rem,auto)]"
)


def _field(label: str, control: rx.Component) -> rx.Component:
    return rx.el.div(
        rx.el.label(label, class_name=design.LABEL),
        control,
        class_name="space-y-1",
    )


def _farm_option(farm: FarmOption) -> rx.Component:
    return rx.el.option(farm["label"], value=farm["id"].to_string())


def _listing_option(item: MyListing) -> rx.Component:
    return rx.el.option(item["crop"], value=item["id"].to_string())


def _listing_row(item: MyListing) -> rx.Component:
    return rx.el.li(
        rx.el.div(
            rx.el.p(
                rx.cond(LanguageState.is_telugu, item["crop_te"], item["crop"]),
                class_name="font-semibold text-[#123524]",
            ),
            rx.el.span(item["status"], class_name=design.BADGE_NEUTRAL),
            class_name="flex items-center justify-between gap-2",
        ),
        rx.el.p(
            f"\u20b9{item['price']:.2f} / {item['unit']} \u00b7 "
            f"{item['quantity']:.1f} {item['unit']} left",
            class_name=design.HELPER,
        ),
        rx.el.div(
            rx.el.span(item["freshness"], class_name=design.BADGE_FRESH),
            rx.cond(
                item["same_day"],
                rx.el.span(
                    "Photo proof today", class_name=design.BADGE_VERIFIED
                ),
                rx.el.span(
                    "No same-day photo", class_name=design.BADGE_NEUTRAL
                ),
            ),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.div(
            rx.el.span(
                f"{item['views']} views \u00b7 {item['interest']} interested",
                class_name=design.HELPER,
            ),
            rx.el.div(
                rx.el.button(
                    "Edit",
                    on_click=lambda: FarmerStudioState.edit_listing(item["id"]),
                    class_name=design.BUTTON_SECONDARY + " py-1.5",
                ),
                rx.el.button(
                    "Unpublish",
                    on_click=lambda: FarmerStudioState.unpublish_listing(
                        item["id"]
                    ),
                    class_name=design.BUTTON_SECONDARY + " py-1.5",
                ),
                class_name="flex items-center gap-2",
            ),
            class_name="flex flex-wrap items-center justify-between gap-2",
        ),
        class_name="space-y-2 rounded-xl border border-[#E7DCC8] bg-white p-3",
    )


def _listing_form() -> rx.Component:
    return rx.el.form(
        rx.el.h1("Create or edit crop listing", class_name=design.HEADING_LG),
        rx.el.p(
            "\u0c2e\u0c40 \u0c2a\u0c02\u0c1f \u0c35\u0c3f\u0c35\u0c30\u0c3e\u0c32\u0c41",
            class_name=design.TELUGU_TEXT + " text-sm text-[#4A3F35]",
        ),
        rx.el.div(
            _field(
                "Crop (English)",
                rx.el.input(
                    name="crop",
                    placeholder="Tomato",
                    class_name=design.INPUT,
                ),
            ),
            _field(
                "Crop (Telugu)",
                rx.el.input(
                    name="crop_te",
                    placeholder="\u0c1f\u0c2e\u0c3e\u0c1f",
                    class_name=design.INPUT + " font-['Noto_Sans_Telugu']",
                ),
            ),
            _field(
                "Quantity",
                rx.el.input(
                    name="quantity",
                    type="number",
                    step="0.1",
                    placeholder="120",
                    class_name=design.INPUT,
                ),
            ),
            _field(
                "Unit",
                rx.el.select(
                    rx.el.option("Kilogram", value="kg"),
                    rx.el.option("Quintal", value="quintal"),
                    rx.el.option("Crate", value="crate"),
                    rx.el.option("Bundle", value="bundle"),
                    rx.el.option("Dozen", value="dozen"),
                    name="unit",
                    default_value="kg",
                    class_name=design.INPUT + " appearance-none",
                ),
            ),
            _field(
                "Price per unit (\u20b9)",
                rx.el.input(
                    name="price",
                    type="number",
                    step="0.5",
                    placeholder="24",
                    class_name=design.INPUT,
                ),
            ),
            _field(
                "Harvest date",
                rx.el.input(
                    name="harvest_date",
                    type="date",
                    max=FarmerStudioState.today_label,
                    class_name=design.INPUT,
                ),
            ),
            _field(
                "Farm location",
                rx.el.select(
                    rx.el.option("Select a farm", value=""),
                    rx.foreach(FarmerStudioState.farms, _farm_option),
                    name="farm_id",
                    class_name=design.INPUT + " appearance-none",
                ),
            ),
            _field(
                "Publish as",
                rx.el.select(
                    rx.el.option("Live in the marketplace", value="live"),
                    rx.el.option("Save as draft", value="draft"),
                    name="publish",
                    default_value="live",
                    class_name=design.INPUT + " appearance-none",
                ),
            ),
            _field(
                "Description for buyers",
                rx.el.input(
                    name="description",
                    placeholder="Grading, packing, transport notes\u2026",
                    class_name=design.INPUT,
                ),
            ),
            class_name="grid grid-cols-1 gap-3 md:grid-cols-2",
        ),
        rx.el.div(
            rx.el.button(
                rx.icon("save", class_name="h-4 w-4"),
                rx.cond(
                    FarmerStudioState.editing_id > 0,
                    "Update listing",
                    "Publish listing",
                ),
                type="submit",
                class_name=design.BUTTON_PRIMARY,
            ),
            rx.el.button(
                "Clear form",
                type="button",
                on_click=FarmerStudioState.clear_form,
                class_name=design.BUTTON_SECONDARY,
            ),
            class_name="flex flex-wrap items-center gap-3",
        ),
        rx.cond(
            FarmerStudioState.error != "",
            rx.el.p(
                FarmerStudioState.error,
                class_name="text-sm font-medium text-red-600",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FarmerStudioState.message != "",
            rx.el.p(
                FarmerStudioState.message,
                class_name="text-sm font-semibold text-[#1B5E3A]",
            ),
            rx.fragment(),
        ),
        on_submit=FarmerStudioState.save_listing,
        reset_on_submit=True,
        id="listing-form",
        class_name=(
            "col-span-12 lg:col-start-1 lg:col-span-7 lg:row-start-2 "
            "lg:row-span-9 space-y-4 overflow-y-auto rounded-xl border "
            "border-[#E7DCC8] bg-white p-5"
        ),
    )


def _photo_upload() -> rx.Component:
    return rx.el.section(
        rx.el.h3("Today\u2019s photo proof", class_name=design.HEADING_MD),
        rx.el.p(
            f"Only photos captured on {FarmerStudioState.today_label} count as "
            "same-day proof.",
            class_name=design.HELPER,
        ),
        rx.el.select(
            rx.el.option("Choose listing", value="0"),
            rx.foreach(FarmerStudioState.my_listings, _listing_option),
            value=FarmerStudioState.photo_listing_id.to_string(),
            on_change=FarmerStudioState.set_photo_listing,
            class_name=design.INPUT + " appearance-none",
        ),
        rx.el.input(
            type="date",
            max=FarmerStudioState.today_label,
            default_value=FarmerStudioState.capture_date,
            on_change=FarmerStudioState.set_capture_date,
            class_name=design.INPUT,
        ),
        rx.upload.root(
            rx.el.div(
                rx.icon("camera", class_name="h-5 w-5 text-[#1B5E3A]"),
                rx.el.p(
                    "Capture or drop a harvest photo",
                    class_name=design.LABEL,
                ),
                class_name="flex flex-col items-center gap-1 py-4",
            ),
            id="photo_proof",
            accept={"image/*": [".png", ".jpg", ".jpeg", ".webp"]},
            max_files=1,
            class_name="rounded-xl border border-dashed border-[#227A4B] bg-[#F6EFE2]",
        ),
        rx.el.button(
            "Save same-day proof",
            on_click=FarmerStudioState.handle_photo(
                rx.upload_files(upload_id="photo_proof")
            ),
            class_name=design.BUTTON_ACCENT,
        ),
        rx.cond(
            FarmerStudioState.photo_url != "",
            rx.image(
                src=FarmerStudioState.photo_url,
                class_name="h-28 w-full rounded-xl object-cover",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FarmerStudioState.photo_status != "",
            rx.el.p(
                FarmerStudioState.photo_status,
                class_name="text-sm font-semibold text-[#C9860B]",
            ),
            rx.fragment(),
        ),
        id="photo-upload",
        class_name=(
            "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-2 "
            "lg:row-span-4 space-y-3 overflow-y-auto rounded-xl border "
            "border-[#E7DCC8] bg-white p-5"
        ),
    )


def _voice_intro() -> rx.Component:
    return rx.el.form(
        rx.el.h3("Voice introduction", class_name=design.HEADING_MD),
        rx.el.p(
            "Record a short Telugu or English hello so buyers trust you.",
            class_name=design.HELPER,
        ),
        rx.el.select(
            rx.el.option(
                "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41 (Telugu)", value="te"
            ),
            rx.el.option("English", value="en"),
            value=FarmerStudioState.voice_language,
            on_change=FarmerStudioState.set_voice_language,
            class_name=design.INPUT + " appearance-none",
        ),
        rx.upload.root(
            rx.el.div(
                rx.icon("mic", class_name="h-5 w-5 text-[#1B5E3A]"),
                rx.el.p("Add a recording", class_name=design.LABEL),
                class_name="flex flex-col items-center gap-1 py-3",
            ),
            id="voice_intro",
            accept={"audio/*": [".webm", ".mp3", ".m4a", ".wav", ".ogg"]},
            max_files=1,
            class_name="rounded-xl border border-dashed border-[#227A4B] bg-[#F6EFE2]",
        ),
        rx.el.button(
            "Save introduction",
            type="button",
            on_click=FarmerStudioState.handle_voice(
                rx.upload_files(upload_id="voice_intro")
            ),
            class_name=design.BUTTON_PRIMARY,
        ),
        rx.cond(
            FarmerStudioState.voice_url != "",
            rx.audio(
                url=FarmerStudioState.voice_url,
                controls=True,
                width="100%",
                height="42px",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FarmerStudioState.voice_status != "",
            rx.el.p(
                FarmerStudioState.voice_status,
                class_name="text-sm font-semibold text-[#1B5E3A]",
            ),
            rx.fragment(),
        ),
        id="voice-intro",
        class_name=(
            "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-6 "
            "lg:row-span-3 space-y-3 overflow-y-auto rounded-xl border "
            "border-[#E7DCC8] bg-[#F6EFE2] p-5"
        ),
    )


def farmer_studio_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            site_nav("farmer-nav", "Sell Produce"),
            _listing_form(),
            _photo_upload(),
            _voice_intro(),
            rx.el.section(
                rx.el.h3("Current listings", class_name=design.HEADING_MD),
                rx.cond(
                    FarmerStudioState.loading,
                    rx.el.div(
                        class_name="h-24 animate-pulse rounded-xl bg-[#F6EFE2]"
                    ),
                    rx.cond(
                        FarmerStudioState.my_listings.length() == 0,
                        rx.el.p(
                            "No listings yet. Publish your first harvest on "
                            "the left.",
                            class_name=design.HELPER,
                        ),
                        rx.el.ul(
                            rx.foreach(
                                FarmerStudioState.my_listings,
                                _listing_row,
                            ),
                            class_name="space-y-2",
                        ),
                    ),
                ),
                id="farmer-listings",
                class_name=(
                    "col-span-12 lg:col-start-8 lg:col-span-5 lg:row-start-9 "
                    "lg:row-span-4 space-y-3 overflow-y-auto rounded-xl "
                    "border border-[#E7DCC8] bg-white p-5"
                ),
            ),
            class_name=_GRID,
        ),
        class_name=design.APP_SHELL,
    )
