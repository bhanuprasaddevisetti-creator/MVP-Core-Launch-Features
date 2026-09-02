"""Sanity checks for the seed helpers and shared utilities."""

from __future__ import annotations

import datetime as dt

from app.security import hash_password, verify_password
from app.seed import ADVISORY_ROWS, MANDI_ROWS, seed_database
from app.utils import (
    format_distance,
    format_freshness,
    haversine_km,
    next_radius_km,
    price_gap_percent,
    quintal_to_kg_price,
    slugify,
)


def test_password_round_trip() -> None:
    stored = hash_password("field-to-market")
    assert "field-to-market" not in stored
    assert verify_password("field-to-market", stored)
    assert not verify_password("wrong", stored)


def test_utils() -> None:
    assert slugify("Red Gram (Tur)") == "red-gram-tur"
    assert haversine_km(17.6, 78.5, 17.6, 78.5) == 0.0
    assert haversine_km(None, 78.5, 17.6, 78.5) is None
    assert next_radius_km(10.0) == 25.0
    assert next_radius_km(100.0) is None
    assert "km away" in format_distance(4.2)
    assert format_freshness(dt.date.today()) == "Harvested today"
    assert quintal_to_kg_price(1650.0) == 16.5
    assert price_gap_percent(22.0, 16.5) == 33.3


def test_content_rows_are_bilingual_and_unique() -> None:
    slugs = [r["slug"] for r in ADVISORY_ROWS]
    assert len(slugs) == len(set(slugs))
    for row in ADVISORY_ROWS:
        assert row["title_te"] and row["summary_te"] and row["body_te"]
    keys = {(r["crop_en"], r["mandi"]) for r in MANDI_ROWS}
    assert len(keys) == len(MANDI_ROWS)


def test_seed_is_idempotent() -> None:
    seed_database()
    second = seed_database()
    assert second == {
        "mandi_prices": 0,
        "advisory_entries": 0,
        "demo_listings": 0,
    }
