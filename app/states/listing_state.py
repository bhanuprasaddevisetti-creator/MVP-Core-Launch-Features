import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.states.marketplace_state import photo_src
from app.utils import (
    format_distance,
    format_freshness,
    haversine_km,
    price_gap_percent,
)


class AdviceTip(TypedDict):
    id: int
    title: str
    title_te: str
    summary: str
    source: str
    url: str


_DETAIL_SQL = """
SELECT l.id,
       l.crop_name_en,
       COALESCE(l.crop_name_te, ''),
       COALESCE(l.crop_slug, ''),
       COALESCE(l.variety, ''),
       COALESCE(l.description_en, ''),
       COALESCE(l.description_te, ''),
       COALESCE(l.price_per_unit, 0),
       l.unit,
       COALESCE(l.quantity_available, 0),
       COALESCE(l.min_order_quantity, 1),
       l.harvest_date,
       l.listed_at,
       COALESCE(l.mandi_reference_price, 0),
       COALESCE(l.mandi_reference_name, ''),
       COALESCE(l.offers_delivery, false),
       COALESCE(l.offers_pickup, true),
       COALESCE(f.village, ''),
       COALESCE(f.mandal, ''),
       COALESCE(f.district, 'Telangana'),
       f.latitude,
       f.longitude,
       COALESCE(fp.display_name, ''),
       COALESCE(fp.display_name_te, ''),
       COALESCE(fp.bio_en, ''),
       COALESCE(fp.bio_te, ''),
       fp.verification_status,
       COALESCE(fp.is_local_partner, false),
       COALESCE(
           (SELECT p.file_name FROM crop_photo_proof p
            WHERE p.listing_id = l.id ORDER BY p.created_at DESC LIMIT 1), ''),
       (SELECT p.capture_date FROM crop_photo_proof p
        WHERE p.listing_id = l.id ORDER BY p.created_at DESC LIMIT 1),
       COALESCE(
           (SELECT p.is_same_day FROM crop_photo_proof p
            WHERE p.listing_id = l.id ORDER BY p.created_at DESC LIMIT 1),
           false),
       COALESCE(
           (SELECT v.file_name FROM voice_introduction v
            WHERE v.farmer_id = fp.id AND v.is_active = true
            ORDER BY v.created_at DESC LIMIT 1), '')
FROM crop_listing l
LEFT JOIN farm f ON f.id = l.farm_id
JOIN farmer_profile fp ON fp.id = l.farmer_id
WHERE l.id = :listing_id
"""


class ListingState(rx.State):
    listing: dict[str, str | float | bool | int] = {
        "id": 0,
        "crop": "",
        "crop_te": "",
        "variety": "",
        "description": "",
        "description_te": "",
        "price": 0.0,
        "unit": "kg",
        "quantity": 0.0,
        "min_order": 1.0,
        "freshness": "",
        "harvest": "",
        "listed_label": "",
        "mandi_price": 0.0,
        "mandi_name": "",
        "mandi_delta": 0.0,
        "distance_label": "",
        "village": "",
        "mandal": "",
        "district": "",
        "farmer": "",
        "farmer_te": "",
        "bio": "",
        "bio_te": "",
        "verified": False,
        "local_partner": False,
        "image": "/documentary_editorial_telangana.png",
        "capture_date": "",
        "same_day": False,
        "offers_delivery": False,
        "offers_pickup": True,
    }
    voice_file: str = ""
    tips: list[AdviceTip] = []
    loading: bool = False
    error: str = ""

    draft_quantity: str = ""
    draft_mode: str = "farm_pickup"
    draft_note: str = ""
    draft_error: str = ""
    draft_ready: bool = False

    @rx.var
    def voice_url(self) -> str:
        return photo_src(self.voice_file) if self.voice_file else ""

    @rx.var
    def draft_total(self) -> float:
        try:
            qty = float(self.draft_quantity or 0)
        except ValueError:
            return 0.0
        return round(qty * float(self.listing["price"]), 2)

    @rx.event
    def set_draft_mode(self, value: str):
        self.draft_mode = value

    @rx.event
    def prepare_draft(self, form_data: dict[str, Any]):
        self.draft_quantity = str(form_data.get("quantity", "")).strip()
        self.draft_note = str(form_data.get("note", "")).strip()
        self.draft_mode = str(form_data.get("mode", self.draft_mode))
        self.draft_ready = False
        self.draft_error = ""
        if self.listing["id"] == 0:
            self.draft_error = "This harvest is no longer available."
            return
        try:
            qty = float(self.draft_quantity)
        except ValueError:
            self.draft_error = "Enter the quantity you need as a number."
            return
        if qty < float(self.listing["min_order"]):
            self.draft_error = (
                f"Minimum order is {self.listing['min_order']} "
                f"{self.listing['unit']}."
            )
            return
        if qty > float(self.listing["quantity"]):
            self.draft_error = (
                f"Only {self.listing['quantity']} {self.listing['unit']} "
                "remain available."
            )
            return
        if (
            self.draft_mode == "local_delivery"
            and not self.listing["offers_delivery"]
        ):
            self.draft_error = "This farmer offers farm pickup only."
            return
        self.draft_ready = True

    @rx.event(background=True)
    async def load_listing(self):
        async with self:
            listing_id = self.router.page.params.get("id", "")
            self.loading = True
            self.draft_ready = False
            self.draft_error = ""
            buyer_lat, buyer_lon = None, None
        try:
            from app.states.marketplace_state import MarketplaceState

            async with self:
                market = await self.get_state(MarketplaceState)
                buyer_lat, buyer_lon = market.latitude, market.longitude
            async with rx.asession() as asession:
                row = (
                    await asession.execute(
                        text(_DETAIL_SQL), {"listing_id": int(listing_id or 0)}
                    )
                ).first()
                if row is None:
                    async with self:
                        self.error = "That harvest listing was not found."
                        self.loading = False
                    return
                tip_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, title_en, COALESCE(title_te, ''),
                                   COALESCE(summary_en, ''),
                                   COALESCE(source_name, ''),
                                   COALESCE(source_url, '')
                            FROM advisory_entry
                            WHERE is_published = true
                              AND (crop_slug = :slug OR crop_slug = '')
                            ORDER BY CASE WHEN crop_slug = :slug THEN 0
                                          ELSE 1 END, reviewed_on DESC
                            LIMIT 3
                            """
                        ),
                        {"slug": str(row[3])},
                    )
                ).all()

            price = float(row[7])
            mandi = float(row[13])
            delta = price_gap_percent(price, mandi) if mandi else None
            distance = haversine_km(buyer_lat, buyer_lon, row[20], row[21])
            async with self:
                self.listing = {
                    "id": int(row[0]),
                    "crop": str(row[1]),
                    "crop_te": str(row[2]),
                    "variety": str(row[4]),
                    "description": str(row[5]),
                    "description_te": str(row[6]),
                    "price": price,
                    "unit": str(row[8]).lower(),
                    "quantity": float(row[9]),
                    "min_order": float(row[10]),
                    "freshness": format_freshness(row[11]),
                    "harvest": str(row[11] or "pending"),
                    "listed_label": (
                        f"Listed {row[12].strftime('%d %b %Y, %H:%M')}"
                        if row[12]
                        else "Listed recently"
                    ),
                    "mandi_price": mandi,
                    "mandi_name": str(row[14]),
                    "mandi_delta": float(delta) if delta else 0.0,
                    "distance_label": format_distance(distance),
                    "village": str(row[17]),
                    "mandal": str(row[18]),
                    "district": str(row[19]),
                    "farmer": str(row[22]),
                    "farmer_te": str(row[23]),
                    "bio": str(row[24]),
                    "bio_te": str(row[25]),
                    "verified": str(row[26]).upper() == "VERIFIED",
                    "local_partner": bool(row[27]),
                    "image": photo_src(row[28]),
                    "capture_date": str(row[29] or ""),
                    "same_day": bool(row[30]),
                    "offers_delivery": bool(row[15]),
                    "offers_pickup": bool(row[16]),
                }
                self.voice_file = str(row[31])
                self.tips = [
                    {
                        "id": int(t[0]),
                        "title": str(t[1]),
                        "title_te": str(t[2]),
                        "summary": str(t[3]),
                        "source": str(t[4]),
                        "url": str(t[5]),
                    }
                    for t in tip_rows
                ]
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "This harvest could not be loaded."
        finally:
            async with self:
                self.loading = False
