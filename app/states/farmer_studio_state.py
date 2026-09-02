import datetime as dt
import logging
import secrets
from typing import Any, TypedDict

import reflex as rx
from sqlalchemy import text

from app.models import (
    CropListing,
    CropPhotoProof,
    ListingStatus,
    QuantityUnit,
    VoiceIntroduction,
)
from app.states.marketplace_state import photo_src
from app.utils import format_freshness, slugify


class FarmOption(TypedDict):
    id: int
    label: str


class MyListing(TypedDict):
    id: int
    crop: str
    crop_te: str
    price: float
    unit: str
    quantity: float
    status: str
    freshness: str
    views: int
    interest: int
    same_day: bool


class FarmerStudioState(rx.State):
    farmer_id: int = 0
    farms: list[FarmOption] = []
    my_listings: list[MyListing] = []
    editing_id: int = 0
    loading: bool = False
    error: str = ""
    message: str = ""

    capture_date: str = ""
    photo_file: str = ""
    photo_status: str = ""
    photo_listing_id: int = 0

    voice_file: str = ""
    voice_language: str = "te"
    voice_status: str = ""

    @rx.var
    def photo_url(self) -> str:
        return photo_src(self.photo_file) if self.photo_file else ""

    @rx.var
    def voice_url(self) -> str:
        return photo_src(self.voice_file) if self.voice_file else ""

    @rx.var
    def today_label(self) -> str:
        return dt.date.today().isoformat()

    @rx.event
    def set_capture_date(self, value: str):
        self.capture_date = value

    @rx.event
    def set_voice_language(self, value: str):
        self.voice_language = value

    @rx.event
    def set_photo_listing(self, value: str):
        try:
            self.photo_listing_id = int(value)
        except ValueError:
            self.photo_listing_id = 0

    @rx.event
    def clear_form(self):
        self.editing_id = 0
        self.message = ""
        self.error = ""

    @rx.event
    def edit_listing(self, listing_id: int):
        self.editing_id = listing_id
        self.message = "Editing an existing listing \u2014 save to update it."

    @rx.event
    async def guard(self):
        """Role guard: only verified-in farmers may open the studio."""
        from app.states.auth_state import AuthState

        auth = await self.get_state(AuthState)
        if auth.user_id == 0:
            return rx.redirect("/login")
        if auth.role != "farmer":
            return rx.redirect("/marketplace")
        return FarmerStudioState.load_studio

    @rx.event(background=True)
    async def load_studio(self):
        from app.states.auth_state import AuthState

        async with self:
            self.loading = True
            auth = await self.get_state(AuthState)
            user_id = auth.user_id
        try:
            async with rx.asession() as asession:
                profile = (
                    await asession.execute(
                        text(
                            "SELECT id FROM farmer_profile "
                            "WHERE user_id = :uid LIMIT 1"
                        ),
                        {"uid": user_id},
                    )
                ).first()
                if profile is None:
                    async with self:
                        self.farmer_id = 0
                        self.error = (
                            "No farmer profile is linked to this account yet."
                        )
                        self.loading = False
                    return
                farmer_id = int(profile[0])
                farm_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, COALESCE(name, ''),
                                   COALESCE(village, ''),
                                   COALESCE(district, '')
                            FROM farm
                            WHERE farmer_id = :fid AND is_active = true
                            ORDER BY is_primary DESC, id
                            LIMIT 20
                            """
                        ),
                        {"fid": farmer_id},
                    )
                ).all()
                listing_rows = (
                    await asession.execute(
                        text(
                            """
                            SELECT id, crop_name_en, COALESCE(crop_name_te, ''),
                                   COALESCE(price_per_unit, 0), unit,
                                   COALESCE(quantity_available, 0), status,
                                   harvest_date, COALESCE(view_count, 0),
                                   COALESCE(interest_count, 0),
                                   COALESCE(has_same_day_proof, false)
                            FROM crop_listing
                            WHERE farmer_id = :fid
                            ORDER BY listed_at DESC
                            LIMIT 40
                            """
                        ),
                        {"fid": farmer_id},
                    )
                ).all()
                voice = (
                    await asession.execute(
                        text(
                            "SELECT file_name FROM voice_introduction "
                            "WHERE farmer_id = :fid AND is_active = true "
                            "ORDER BY created_at DESC LIMIT 1"
                        ),
                        {"fid": farmer_id},
                    )
                ).first()
            async with self:
                self.farmer_id = farmer_id
                self.farms = [
                    {
                        "id": int(r[0]),
                        "label": f"{r[1] or 'Farm'} \u00b7 {r[2]}, {r[3]}",
                    }
                    for r in farm_rows
                ]
                self.my_listings = [
                    {
                        "id": int(r[0]),
                        "crop": str(r[1]),
                        "crop_te": str(r[2]),
                        "price": float(r[3]),
                        "unit": str(r[4]).lower(),
                        "quantity": float(r[5]),
                        "status": str(r[6]).lower(),
                        "freshness": format_freshness(r[7]),
                        "views": int(r[8]),
                        "interest": int(r[9]),
                        "same_day": bool(r[10]),
                    }
                    for r in listing_rows
                ]
                if voice is not None:
                    self.voice_file = str(voice[0])
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "The studio could not be loaded."
        finally:
            async with self:
                self.loading = False

    @rx.event
    async def save_listing(self, form_data: dict[str, Any]):
        self.error = ""
        self.message = ""
        crop = str(form_data.get("crop", "")).strip()
        crop_te = str(form_data.get("crop_te", "")).strip()
        unit = str(form_data.get("unit", "kg")).strip().lower()
        harvest = str(form_data.get("harvest_date", "")).strip()
        farm_raw = str(form_data.get("farm_id", "")).strip()
        publish = str(form_data.get("publish", "live")).strip()
        if self.farmer_id == 0:
            self.error = "Your farmer profile is not ready yet."
            return
        if len(crop) < 2:
            self.error = "Enter the crop name."
            return
        try:
            quantity = float(form_data.get("quantity", 0) or 0)
            price = float(form_data.get("price", 0) or 0)
        except ValueError:
            self.error = "Quantity and price must be numbers."
            return
        if quantity <= 0 or price <= 0:
            self.error = "Quantity and price must both be greater than zero."
            return
        harvest_date: dt.date | None = None
        if harvest:
            try:
                harvest_date = dt.date.fromisoformat(harvest)
            except ValueError:
                self.error = "Harvest date must be a real date."
                return
            if harvest_date > dt.date.today():
                self.error = "Harvest date cannot be in the future."
                return
        status = (
            ListingStatus.LIVE if publish == "live" else ListingStatus.DRAFT
        )
        try:
            async with rx.asession() as asession:
                if self.editing_id > 0:
                    await asession.execute(
                        text(
                            """
                            UPDATE crop_listing
                            SET crop_name_en = :crop, crop_name_te = :crop_te,
                                crop_slug = :slug, quantity_available = :qty,
                                quantity_total = :qty, price_per_unit = :price,
                                unit = :unit, harvest_date = :harvest,
                                farm_id = :farm_id, status = :status,
                                description_en = :desc, updated_at = NOW()
                            WHERE id = :lid AND farmer_id = :fid
                            """
                        ),
                        {
                            "crop": crop,
                            "crop_te": crop_te,
                            "slug": slugify(crop),
                            "qty": quantity,
                            "price": price,
                            "unit": QuantityUnit(unit).name,
                            "harvest": harvest_date,
                            "farm_id": int(farm_raw) if farm_raw else None,
                            "status": status.name,
                            "desc": str(
                                form_data.get("description", "")
                            ).strip(),
                            "lid": self.editing_id,
                            "fid": self.farmer_id,
                        },
                    )
                    self.message = "Listing updated."
                else:
                    listing = CropListing(
                        farmer_id=self.farmer_id,
                        farm_id=int(farm_raw) if farm_raw else None,
                        crop_name_en=crop,
                        crop_name_te=crop_te,
                        crop_slug=slugify(crop),
                        description_en=str(
                            form_data.get("description", "")
                        ).strip(),
                        quantity_total=quantity,
                        quantity_available=quantity,
                        unit=QuantityUnit(unit),
                        price_per_unit=price,
                        harvest_date=harvest_date,
                        status=status,
                    )
                    asession.add(listing)
                    await asession.flush()
                    self.photo_listing_id = int(listing.id)
                    self.message = (
                        "Listing saved. Add today's photo proof so buyers "
                        "trust the freshness."
                    )
                await asession.commit()
            self.editing_id = 0
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "We could not save that listing. Please try again."
            return
        return FarmerStudioState.load_studio

    @rx.event
    async def unpublish_listing(self, listing_id: int):
        try:
            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        "UPDATE crop_listing SET status = 'UNPUBLISHED', "
                        "unpublished_at = NOW(), updated_at = NOW() "
                        "WHERE id = :lid AND farmer_id = :fid"
                    ),
                    {"lid": listing_id, "fid": self.farmer_id},
                )
                await asession.commit()
            self.message = "Listing unpublished."
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "That listing could not be unpublished."
        return FarmerStudioState.load_studio

    @rx.event
    async def handle_photo(self, files: list[rx.UploadFile]):
        self.photo_status = ""
        self.error = ""
        today = dt.date.today()
        if not files:
            self.photo_status = "Choose a photo captured today."
            return
        if self.photo_listing_id == 0:
            self.photo_status = "Pick which listing this photo belongs to."
            return
        if self.capture_date and self.capture_date != today.isoformat():
            self.photo_status = (
                "Same-day proof only: the capture date must be "
                f"{today.isoformat()}."
            )
            return
        try:
            upload = files[0]
            data = await upload.read()
            if not data:
                self.photo_status = "That file was empty."
                return
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            name = f"upload_{secrets.token_hex(6)}_{upload.name}"
            (upload_dir / name).write_bytes(data)
            now = dt.datetime.now(dt.timezone.utc)
            async with rx.asession() as asession:
                asession.add(
                    CropPhotoProof(
                        listing_id=self.photo_listing_id,
                        file_name=name,
                        mime_type=upload.content_type or "image/jpeg",
                        file_size_bytes=len(data),
                        captured_at=now,
                        capture_date=today,
                        capture_source="camera",
                        is_same_day=True,
                        is_primary=True,
                        caption_en="Same-day harvest proof",
                    )
                )
                await asession.execute(
                    text(
                        "UPDATE crop_listing SET has_same_day_proof = true, "
                        "updated_at = NOW() WHERE id = :lid AND farmer_id = :fid"
                    ),
                    {"lid": self.photo_listing_id, "fid": self.farmer_id},
                )
                await asession.commit()
            self.photo_file = name
            self.photo_status = f"Same-day proof saved for {today.isoformat()}."
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.photo_status = "The photo could not be saved."
            return
        return FarmerStudioState.load_studio

    @rx.event
    async def handle_voice(self, files: list[rx.UploadFile]):
        self.voice_status = ""
        if not files:
            self.voice_status = "Choose a short audio file to upload."
            return
        if self.farmer_id == 0:
            self.voice_status = "Your farmer profile is not ready yet."
            return
        try:
            upload = files[0]
            data = await upload.read()
            if len(data) > 8 * 1024 * 1024:
                self.voice_status = "Keep the introduction under 8 MB."
                return
            upload_dir = rx.get_upload_dir()
            upload_dir.mkdir(parents=True, exist_ok=True)
            name = f"upload_{secrets.token_hex(6)}_{upload.name}"
            (upload_dir / name).write_bytes(data)
            from app.models import LanguagePref

            async with rx.asession() as asession:
                await asession.execute(
                    text(
                        "UPDATE voice_introduction SET is_active = false "
                        "WHERE farmer_id = :fid"
                    ),
                    {"fid": self.farmer_id},
                )
                asession.add(
                    VoiceIntroduction(
                        farmer_id=self.farmer_id,
                        file_name=name,
                        mime_type=upload.content_type or "audio/webm",
                        file_size_bytes=len(data),
                        language=LanguagePref(self.voice_language),
                        is_active=True,
                    )
                )
                await asession.commit()
            self.voice_file = name
            self.voice_status = "Voice introduction saved and playable below."
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.voice_status = "The recording could not be saved."
