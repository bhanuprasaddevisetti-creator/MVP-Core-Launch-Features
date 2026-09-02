import datetime as dt
import logging
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.utils import (
    RADIUS_STEPS_KM,
    format_distance,
    format_freshness,
    haversine_km,
    price_gap_percent,
)

GEOLOCATION_SCRIPT = """
new Promise((resolve) => {
  if (!navigator.geolocation) { resolve([]); return; }
  navigator.geolocation.getCurrentPosition(
    (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
    () => resolve([]),
    { enableHighAccuracy: true, timeout: 8000 }
  );
})
"""


def photo_src(file_name: str) -> str:
    """Resolve a stored proof file name to a browser-usable image URL."""
    if not file_name:
        return "/documentary_editorial_telangana.png"
    if file_name.startswith("upload_"):
        return f"/_upload/{file_name}"
    return f"/{file_name.lstrip('/')}"


class ListingCard(TypedDict):
    id: int
    crop: str
    crop_te: str
    price: float
    unit: str
    quantity: float
    distance: float
    distance_label: str
    farmer: str
    verified: bool
    local_partner: bool
    same_day: bool
    freshness: str
    listed_label: str
    mandi_price: float
    mandi_name: str
    mandi_delta: float
    district: str
    village: str
    image: str
    lat: float
    lon: float


_LISTING_SQL = """
SELECT l.id,
       l.crop_name_en,
       COALESCE(l.crop_name_te, ''),
       COALESCE(l.price_per_unit, 0),
       l.unit,
       COALESCE(l.quantity_available, 0),
       l.harvest_date,
       l.listed_at,
       COALESCE(l.has_same_day_proof, false),
       COALESCE(l.mandi_reference_price, 0),
       COALESCE(l.mandi_reference_name, ''),
       COALESCE(f.district, 'Telangana'),
       COALESCE(f.village, ''),
       f.latitude,
       f.longitude,
       COALESCE(fp.display_name, ''),
       fp.verification_status,
       COALESCE(fp.is_local_partner, false),
       COALESCE(
           (SELECT p.file_name FROM crop_photo_proof p
            WHERE p.listing_id = l.id AND p.is_same_day = true
            ORDER BY p.created_at DESC LIMIT 1), '')
FROM crop_listing l
LEFT JOIN farm f ON f.id = l.farm_id
JOIN farmer_profile fp ON fp.id = l.farmer_id
WHERE l.status = 'LIVE' AND l.quantity_available > 0
"""


class MarketplaceState(rx.State):
    listings: list[ListingCard] = []
    query: str = ""
    district: str = ""
    radius_km: float = 10.0
    latitude: float = 17.3850
    longitude: float = 78.4867
    location_status: str = "Using Hyderabad city centre as fallback"
    using_browser_location: bool = False
    radius_notice: str = ""
    verified_only: bool = False
    same_day_only: bool = False
    max_price: float = 0.0
    harvest_within_days: int = 0
    loading: bool = False
    error: str = ""

    @rx.var
    def spotlight(self) -> dict[str, str | float]:
        if not self.listings:
            return {
                "crop": "",
                "farmer_price": 0.0,
                "mandi_price": 0.0,
                "mandi_name": "",
                "delta": 0.0,
                "unit": "kg",
            }
        top = self.listings[0]
        return {
            "crop": str(top["crop"]),
            "farmer_price": float(top["price"]),
            "mandi_price": float(top["mandi_price"]),
            "mandi_name": str(top["mandi_name"]),
            "delta": float(top["mandi_delta"]),
            "unit": str(top["unit"]),
        }

    @rx.var
    def result_summary(self) -> str:
        return (
            f"{len(self.listings)} harvest(s) within {self.radius_km:.0f} km, "
            "nearest first"
        )

    @rx.event
    def set_query(self, value: str):
        self.query = value

    @rx.event
    def set_district(self, value: str):
        self.district = value

    @rx.event
    def set_radius(self, value: str):
        try:
            self.radius_km = float(value)
        except ValueError:
            self.radius_km = 10.0
        return MarketplaceState.load_listings

    @rx.event
    def submit_search(self, form_data: dict[str, Any]):
        self.query = str(form_data.get("query", "")).strip()
        self.district = str(form_data.get("district", "")).strip()
        radius = str(form_data.get("radius", "") or self.radius_km)
        try:
            self.radius_km = float(radius)
        except ValueError:
            pass
        return MarketplaceState.load_listings

    @rx.event
    def toggle_verified(self):
        self.verified_only = not self.verified_only
        return MarketplaceState.load_listings

    @rx.event
    def toggle_same_day(self):
        self.same_day_only = not self.same_day_only
        return MarketplaceState.load_listings

    @rx.event
    def set_max_price(self, value: str):
        try:
            self.max_price = max(float(value), 0.0)
        except ValueError:
            self.max_price = 0.0
        return MarketplaceState.load_listings

    @rx.event
    def set_harvest_window(self, value: str):
        try:
            self.harvest_within_days = int(value)
        except ValueError:
            self.harvest_within_days = 0
        return MarketplaceState.load_listings

    @rx.event
    def request_geolocation(self):
        self.location_status = "Asking your browser for coordinates\u2026"
        return rx.call_script(
            GEOLOCATION_SCRIPT,
            callback=MarketplaceState.apply_geolocation,
        )

    @rx.event
    def apply_geolocation(self, coords: list[float] | None):
        if not coords or len(coords) < 2:
            self.using_browser_location = False
            self.location_status = (
                "Location permission unavailable \u2014 enter a Telangana "
                "district below instead."
            )
            return
        self.latitude = float(coords[0])
        self.longitude = float(coords[1])
        self.using_browser_location = True
        self.location_status = (
            f"Using your location \u00b7 {self.latitude:.4f}, "
            f"{self.longitude:.4f}"
        )
        return MarketplaceState.load_listings

    @rx.event(background=True)
    async def load_listings(self):
        async with self:
            self.loading = True
            query = self.query.strip().lower()
            district = self.district.strip().lower()
            lat, lon = self.latitude, self.longitude
            radius = self.radius_km
            verified_only = self.verified_only
            same_day_only = self.same_day_only
            max_price = self.max_price
            harvest_days = self.harvest_within_days
        try:
            sql = _LISTING_SQL
            params: dict[str, str | float | int] = {}
            if query:
                sql += (
                    " AND (LOWER(l.crop_name_en) LIKE :q"
                    " OR LOWER(COALESCE(l.crop_name_te, '')) LIKE :q"
                    " OR LOWER(COALESCE(l.crop_slug, '')) LIKE :q)"
                )
                params["q"] = f"%{query}%"
            if district:
                sql += " AND LOWER(COALESCE(f.district, '')) LIKE :d"
                params["d"] = f"%{district}%"
            if verified_only:
                sql += " AND fp.verification_status = 'VERIFIED'"
            if same_day_only:
                sql += " AND l.has_same_day_proof = true"
            if max_price > 0:
                sql += " AND l.price_per_unit <= :maxp"
                params["maxp"] = max_price
            if harvest_days > 0:
                sql += " AND l.harvest_date >= :hfrom"
                params["hfrom"] = str(
                    dt.date.today() - dt.timedelta(days=harvest_days)
                )
            sql += " ORDER BY l.listed_at DESC LIMIT 120"

            async with rx.asession() as asession:
                rows = (await asession.execute(text(sql), params)).all()

            records: list[ListingCard] = []
            for row in rows:
                distance = haversine_km(lat, lon, row[13], row[14])
                price = float(row[3])
                mandi = float(row[9])
                delta = price_gap_percent(price, mandi) if mandi else None
                records.append(
                    {
                        "id": int(row[0]),
                        "crop": str(row[1]),
                        "crop_te": str(row[2]),
                        "price": price,
                        "unit": str(row[4]).lower(),
                        "quantity": float(row[5]),
                        "distance": float(distance) if distance else 0.0,
                        "distance_label": format_distance(distance),
                        "farmer": str(row[15]),
                        "verified": str(row[16]).upper() == "VERIFIED",
                        "local_partner": bool(row[17]),
                        "same_day": bool(row[8]),
                        "freshness": format_freshness(row[6]),
                        "listed_label": (
                            f"Listed {row[7].strftime('%d %b, %H:%M')} IST"
                            if row[7]
                            else "Listed recently"
                        ),
                        "mandi_price": mandi,
                        "mandi_name": str(row[10]),
                        "mandi_delta": float(delta) if delta else 0.0,
                        "district": str(row[11]),
                        "village": str(row[12]),
                        "image": photo_src(row[18]),
                        "lat": float(row[13]) if row[13] else lat,
                        "lon": float(row[14]) if row[14] else lon,
                    }
                )

            notice = ""
            effective = radius
            in_radius = [r for r in records if r["distance"] <= effective]
            if records and not in_radius:
                for step in RADIUS_STEPS_KM:
                    widened = [r for r in records if r["distance"] <= step]
                    if widened:
                        effective = step
                        in_radius = widened
                        notice = (
                            f"No harvest within {radius:.0f} km \u2014 radius "
                            f"widened automatically to {step:.0f} km."
                        )
                        break
            if not in_radius:
                in_radius = records
            in_radius.sort(key=lambda item: float(item["distance"]))

            async with self:
                self.listings = in_radius
                self.radius_km = effective
                self.radius_notice = notice
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Listings are temporarily unavailable."
        finally:
            async with self:
                self.loading = False
