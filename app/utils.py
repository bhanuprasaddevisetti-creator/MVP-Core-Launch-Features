"""Foundational, UI-free helpers shared by later marketplace pages."""

from __future__ import annotations

import datetime as dt
import math
import re
import secrets

EARTH_RADIUS_KM = 6371.0088
# Progressive radius expansion used by nearest-first discovery.
RADIUS_STEPS_KM: tuple[float, ...] = (10.0, 25.0, 50.0, 100.0)
QUINTAL_IN_KG = 100.0


def slugify(value: str) -> str:
    """Stable crop slug: 'Tomato (Hybrid)' -> 'tomato-hybrid'."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    return cleaned.strip("-")


def haversine_km(
    lat1: float | None,
    lon1: float | None,
    lat2: float | None,
    lon2: float | None,
) -> float | None:
    """Great-circle distance in km, or None when a coordinate is missing."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    d_lat = p2 - p1
    d_lon = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(d_lon / 2) ** 2
    )
    return round(2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a)), 2)


def next_radius_km(current_km: float) -> float | None:
    """The next progressive-radius step, or None once the widest is reached."""
    for step in RADIUS_STEPS_KM:
        if step > current_km:
            return step
    return None


def format_distance(distance_km: float | None) -> str:
    if distance_km is None:
        return "Distance unknown"
    if distance_km < 1:
        return f"{int(round(distance_km * 1000))} m away"
    return f"{distance_km:.1f} km away"


def freshness_hours(listed_at: dt.datetime | None) -> float | None:
    if listed_at is None:
        return None
    if listed_at.tzinfo is None:
        listed_at = listed_at.replace(tzinfo=dt.timezone.utc)
    delta = dt.datetime.now(dt.timezone.utc) - listed_at
    return max(delta.total_seconds() / 3600.0, 0.0)


def format_freshness(harvest_date: dt.date | None) -> str:
    """Harvest recency phrased for buyers, the freshness centerpiece."""
    if harvest_date is None:
        return "Harvest date pending"
    days = (dt.date.today() - harvest_date).days
    if days <= 0:
        return "Harvested today"
    if days == 1:
        return "Harvested yesterday"
    if days < 7:
        return f"Harvested {days} days ago"
    weeks = days // 7
    return f"Harvested {weeks} week{'s' if weeks > 1 else ''} ago"


def is_same_day(
    captured: dt.datetime | None, reference: dt.date | None = None
) -> bool:
    """True when photo proof was captured on the reference (default: today)."""
    if captured is None:
        return False
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=dt.timezone.utc)
    return captured.date() == (reference or dt.date.today())


def quintal_to_kg_price(price_per_quintal: float) -> float:
    """Mandi prices are per quintal; listings are usually per kg."""
    return round(float(price_per_quintal) / QUINTAL_IN_KG, 2)


def price_gap_percent(farmer_price: float, mandi_price: float) -> float | None:
    """Positive means the farmer offer is above the mandi reference."""
    if not mandi_price:
        return None
    return round(
        ((float(farmer_price) - float(mandi_price)) / float(mandi_price)) * 100,
        1,
    )


def format_inr(amount: float) -> str:
    return f"\u20b9{float(amount):,.2f}"


def new_order_code() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%y%m%d")
    return f"TG-{stamp}-{secrets.token_hex(3).upper()}"
