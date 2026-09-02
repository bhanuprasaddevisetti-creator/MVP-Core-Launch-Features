"""Shared design tokens for the warm field-to-market identity.

Palette: deep leaf green (trust / growth), turmeric gold (freshness accent),
earthy cream (surfaces). Typography is Telugu-aware: the Noto Sans Telugu
family is loaded alongside Inter so Telugu strings never fall back to a
tofu glyph. Imagery strategy is documentary: real produce photography, wide
crops, no illustrations; `/placeholder.svg` stands in until assets exist.
"""

from __future__ import annotations

# ----------------------------------------------------------------- raw colors
LEAF_900 = "#123524"
LEAF_700 = "#1B5E3A"
LEAF_600 = "#227A4B"
LEAF_100 = "#DCEBE0"
TURMERIC_600 = "#C9860B"
TURMERIC_500 = "#E8A317"
TURMERIC_100 = "#FCEFCF"
CREAM_50 = "#FDFAF3"
CREAM_100 = "#F6EFE2"
CREAM_200 = "#E7DCC8"
SOIL_700 = "#4A3F35"

PALETTE: dict[str, str] = {
    "leaf_900": LEAF_900,
    "leaf_700": LEAF_700,
    "leaf_600": LEAF_600,
    "leaf_100": LEAF_100,
    "turmeric_600": TURMERIC_600,
    "turmeric_500": TURMERIC_500,
    "turmeric_100": TURMERIC_100,
    "cream_50": CREAM_50,
    "cream_100": CREAM_100,
    "cream_200": CREAM_200,
    "soil_700": SOIL_700,
}

# ------------------------------------------------------------ tailwind tokens
# Arbitrary-value Tailwind classes so no config extension is required.
APP_SHELL = "font-['Inter'] bg-[#FDFAF3] text-[#123524] min-h-screen"
PAGE_GRID = "grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 md:p-6"

SURFACE_CARD = "bg-white border border-[#E7DCC8] rounded-xl"
SURFACE_MUTED = "bg-[#F6EFE2] border border-[#E7DCC8] rounded-xl"
SURFACE_DEEP = "bg-[#123524] text-[#FDFAF3] rounded-xl"

HEADING_LG = "text-2xl font-semibold text-[#123524] tracking-tight"
HEADING_MD = "text-xl font-semibold text-[#123524]"
LABEL = "text-sm font-semibold text-[#4A3F35]"
BODY = "text-base font-medium text-[#4A3F35]"
HELPER = "text-sm font-medium text-[#4A3F35]/70"

# Telugu-aware typography: apply to any element rendering Telugu text.
TELUGU_TEXT = "font-['Noto_Sans_Telugu'] leading-relaxed"

BUTTON_PRIMARY = (
    "inline-flex items-center justify-center gap-2 rounded-xl bg-[#1B5E3A] "
    "px-4 py-2.5 text-sm font-semibold text-white transition-colors "
    "hover:bg-[#123524] focus:outline-hidden focus:ring-2 "
    "focus:ring-[#227A4B] disabled:opacity-50"
)
BUTTON_SECONDARY = (
    "inline-flex items-center justify-center gap-2 rounded-xl border "
    "border-[#E7DCC8] bg-white px-4 py-2.5 text-sm font-semibold "
    "text-[#123524] transition-colors hover:bg-[#F6EFE2]"
)
BUTTON_ACCENT = (
    "inline-flex items-center justify-center gap-2 rounded-xl "
    "bg-[#E8A317] px-4 py-2.5 text-sm font-semibold text-[#123524] "
    "transition-colors hover:bg-[#C9860B]"
)
INPUT = (
    "w-full rounded-xl border border-[#E7DCC8] bg-white px-4 py-2.5 "
    "text-sm font-medium text-[#123524] placeholder:text-[#4A3F35]/50 "
    "focus:border-[#227A4B] focus:ring-2 focus:ring-[#227A4B] "
    "focus:outline-hidden"
)

# Distance and freshness are the visual centerpiece of every listing surface.
BADGE_DISTANCE = (
    "w-fit inline-flex items-center gap-1 rounded-full bg-[#DCEBE0] "
    "px-2.5 py-1 text-xs font-semibold text-[#1B5E3A]"
)
BADGE_FRESH = (
    "w-fit inline-flex items-center gap-1 rounded-full bg-[#FCEFCF] "
    "px-2.5 py-1 text-xs font-semibold text-[#C9860B]"
)
BADGE_VERIFIED = (
    "w-fit inline-flex items-center gap-1 rounded-full bg-[#123524] "
    "px-2.5 py-1 text-xs font-semibold text-[#FDFAF3]"
)
BADGE_NEUTRAL = (
    "w-fit inline-flex items-center gap-1 rounded-full bg-[#F6EFE2] "
    "px-2.5 py-1 text-xs font-semibold text-[#4A3F35]"
)

# Documentary imagery: 4:3 wide crop frames, warm cream letterboxing.
IMAGE_FRAME = "w-full overflow-hidden rounded-xl bg-[#F6EFE2]"
IMAGE_COVER = "w-full h-full object-cover"
PLACEHOLDER_IMAGE = "/placeholder.svg"

FONT_LINKS_HREF = (
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
    "&family=Noto+Sans+Telugu:wght@400;500;600;700&display=swap"
)
