import reflex as rx

from app import design
from app.components.nav import site_nav
from app.states.advisory_state import AdvisoryArticle, AdvisoryState
from app.states.language_state import LanguageState

_GRID = (
    "grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 md:p-6 "
    "lg:auto-rows-[minmax(3.25rem,auto)]"
)


def _card(article: AdvisoryArticle) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.span(article["topic"], class_name=design.BADGE_NEUTRAL),
            rx.el.span(article["season"], class_name=design.BADGE_FRESH),
            class_name="flex flex-wrap items-center gap-2",
        ),
        rx.el.h3(
            rx.cond(
                LanguageState.is_telugu,
                article["title_te"],
                article["title"],
            ),
            class_name=rx.cond(
                LanguageState.is_telugu,
                "text-base font-semibold text-[#123524] font-['Noto_Sans_Telugu']",
                "text-base font-semibold text-[#123524]",
            ),
        ),
        rx.el.p(
            rx.cond(
                LanguageState.is_telugu,
                article["summary_te"],
                article["summary"],
            ),
            class_name=design.HELPER,
        ),
        rx.el.p(
            f"{article['source']} \u00b7 reviewed {article['reviewed']}",
            class_name="text-xs font-semibold text-[#4A3F35]",
        ),
        rx.el.a(
            "Read guidance",
            href=article["url"],
            target="_blank",
            class_name=design.BUTTON_SECONDARY + " w-full",
        ),
        class_name="space-y-2 rounded-xl border border-[#E7DCC8] bg-white p-4",
    )


def _source_row(article: AdvisoryArticle) -> rx.Component:
    return rx.el.li(
        rx.el.a(
            article["source"],
            href=article["url"],
            target="_blank",
            class_name="text-sm font-semibold text-[#1B5E3A] underline",
        ),
        rx.el.span(
            f" \u00b7 reviewed {article['reviewed']}",
            class_name=design.HELPER,
        ),
        class_name="border-b border-[#E7DCC8] py-1.5",
    )


def advisory_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            site_nav("advisory-nav", "Advisory"),
            rx.el.header(
                rx.el.h1("Trusted crop guidance", class_name=design.HEADING_LG),
                rx.el.p(
                    "\u0c2a\u0c02\u0c1f \u0c38\u0c32\u0c39\u0c3e\u0c32\u0c41",
                    class_name=design.TELUGU_TEXT + " text-base text-[#4A3F35]",
                ),
                rx.el.p(
                    "Every note is sourced from ICAR, KVK or the Telangana "
                    "agriculture department and carries its review date.",
                    class_name=design.BODY,
                ),
                id="advisory-header",
                class_name=(
                    "col-span-12 lg:col-start-1 lg:col-span-8 lg:row-start-2 "
                    "lg:row-span-2 space-y-1 rounded-xl border "
                    "border-[#E7DCC8] bg-white p-5"
                ),
            ),
            rx.el.form(
                rx.el.h2("Find advice", class_name="text-base font-semibold"),
                rx.el.input(
                    name="search",
                    placeholder="Crop or topic\u2026",
                    default_value=AdvisoryState.search,
                    class_name=design.INPUT,
                ),
                rx.el.div(
                    rx.el.select(
                        rx.el.option("All seasons", value="all"),
                        rx.el.option("Kharif", value="kharif"),
                        rx.el.option("Rabi", value="rabi"),
                        rx.el.option("Zaid", value="zaid"),
                        rx.el.option("All year", value="all_year"),
                        name="season",
                        default_value=AdvisoryState.season,
                        class_name=design.INPUT + " appearance-none py-1.5",
                    ),
                    rx.el.select(
                        rx.el.option("All topics", value="all"),
                        rx.foreach(
                            AdvisoryState.topics,
                            lambda t: rx.el.option(t, value=t),
                        ),
                        name="topic",
                        default_value=AdvisoryState.topic,
                        class_name=design.INPUT + " appearance-none py-1.5",
                    ),
                    class_name="grid grid-cols-2 gap-2",
                ),
                rx.el.button(
                    rx.icon("search", class_name="h-4 w-4"),
                    "Search advisories",
                    type="submit",
                    class_name=design.BUTTON_PRIMARY + " w-full",
                ),
                on_submit=AdvisoryState.submit_search,
                id="advisory-search",
                class_name=(
                    "col-span-12 lg:col-start-9 lg:col-span-4 lg:row-start-2 "
                    "lg:row-span-2 space-y-2 rounded-xl border "
                    "border-[#E7DCC8] bg-[#F6EFE2] p-4"
                ),
            ),
            rx.el.section(
                rx.el.h2("Advisory articles", class_name=design.HEADING_MD),
                rx.cond(
                    AdvisoryState.loading,
                    rx.el.div(
                        class_name="h-40 animate-pulse rounded-xl bg-[#F6EFE2]"
                    ),
                    rx.cond(
                        AdvisoryState.articles.length() == 0,
                        rx.el.p(
                            "No advisories match that search yet.",
                            class_name=design.HELPER,
                        ),
                        rx.el.div(
                            rx.foreach(AdvisoryState.articles, _card),
                            class_name="grid grid-cols-1 gap-4 md:grid-cols-2",
                        ),
                    ),
                ),
                id="advisory-cards",
                class_name=(
                    "col-span-12 lg:col-start-1 lg:col-span-8 lg:row-start-4 "
                    "lg:row-span-8 space-y-4 overflow-y-auto rounded-xl "
                    "border border-[#E7DCC8] bg-white p-5"
                ),
            ),
            rx.el.aside(
                rx.el.h2("Sources and safety", class_name=design.HEADING_MD),
                rx.el.p(
                    "Guidance is educational. Confirm products, doses and "
                    "timing with your local Agriculture Extension Officer or "
                    "KVK before spraying or sowing.",
                    class_name=design.BODY,
                ),
                rx.el.ul(
                    rx.foreach(AdvisoryState.articles, _source_row),
                    class_name="divide-y divide-[#E7DCC8]",
                ),
                id="advisory-sources",
                class_name=(
                    "col-span-12 lg:col-start-9 lg:col-span-4 lg:row-start-4 "
                    "lg:row-span-8 space-y-3 overflow-y-auto rounded-xl "
                    "border border-[#E7DCC8] bg-[#F6EFE2] p-5"
                ),
            ),
            class_name=_GRID,
        ),
        class_name=design.APP_SHELL,
    )
