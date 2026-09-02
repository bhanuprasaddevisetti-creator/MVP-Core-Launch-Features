"""Sanity checks for the marketplace/advisory read paths and validation."""

from __future__ import annotations

import asyncio
import datetime as dt

from app.states.marketplace_state import photo_src


def test_photo_src_resolution() -> None:
    assert photo_src("") == "/documentary_editorial_telangana.png"
    assert photo_src("placeholder.svg") == "/placeholder.svg"
    assert photo_src("upload_abc_photo.jpg") == "/_upload/upload_abc_photo.jpg"


def test_geolocation_payload_guard() -> None:
    from app.states.marketplace_state import MarketplaceState

    state = MarketplaceState()
    state.apply_geolocation([])
    assert ~state.using_browser_location
    state.apply_geolocation([17.9, 78.1])
    assert state.using_browser_location
    assert round(state.latitude, 1) == 17.9


def test_order_draft_validation() -> None:
    from app.states.listing_state import ListingState

    state = ListingState()
    state.listing = state.listing.copy()
    state.listing.update(
        {
            "id": 1,
            "price": 20.0,
            "unit": "kg",
            "quantity": 50.0,
            "min_order": 5.0,
            "offers_delivery": False,
        }
    )
    state.prepare_draft({"quantity": "2", "note": "", "mode": "farm_pickup"})
    assert ~state.draft_ready
    state.prepare_draft({"quantity": "10", "note": "", "mode": "farm_pickup"})
    assert state.draft_ready
    state.prepare_draft(
        {"quantity": "10", "note": "", "mode": "local_delivery"}
    )
    assert ~state.draft_ready


def test_same_day_photo_rejection() -> None:
    from app.states.farmer_studio_state import FarmerStudioState

    state = FarmerStudioState()
    state.farmer_id = 1
    state.photo_listing_id = 1
    yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    state.capture_date = yesterday
    asyncio.run(_run_photo(state))
    assert state.photo_status.contains("Same-day proof only")


async def _run_photo(state) -> None:
    await state.handle_photo([object()])  # type: ignore[arg-type]
