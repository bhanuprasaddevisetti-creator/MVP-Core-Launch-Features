"""Idempotent starter data for the Telangana marketplace.

Seeds only reference/content data plus clearly marked development records:
  * Telangana mandi reference prices for representative crops
  * sourced static ICAR / KVK advisory entries in English and Telugu
  * three DEMO farmers, farms, live listings and same-day photo proofs so the
    first marketplace view is not empty

No customer activity (orders, payments, chats, disputes, payouts) is invented.
Demo accounts carry an unguessable random password hash that is never
disclosed, so they cannot be signed into.
"""

from __future__ import annotations

import datetime as dt
import logging

import reflex as rx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AdvisoryEntry,
    AdvisorySeason,
    AdvisorySource,
    CropListing,
    CropPhotoProof,
    Farm,
    FarmerProfile,
    LanguagePref,
    ListingStatus,
    MandiPrice,
    ProofReviewStatus,
    QuantityUnit,
    User,
    UserRole,
    VerificationStatus,
    VoiceIntroduction,
)
from app.security import generate_unusable_password
from app.utils import quintal_to_kg_price, slugify

logger = logging.getLogger(__name__)

DEMO_EMAIL_DOMAIN = "demo.telanganafarms.invalid"
DEMO_TAG = "[DEMO DATA]"
DEMO_NOTE_EN = "Development sample record. Not a real farmer or harvest."
DEMO_NOTE_TE = (
    "\u0c05\u0c2d\u0c3f\u0c35\u0c26\u0c4d\u0c27\u0c3f \u0c28\u0c2e\u0c42\u0c28\u0c3e "
    "\u0c30\u0c3f\u0c15\u0c3e\u0c30\u0c4d\u0c21\u0c41."
)


# ------------------------------------------------------------- mandi prices
# Representative Telangana crops with plausible market-yard reference bands,
# quoted per quintal as market yards publish them.
MANDI_ROWS: list[dict[str, str | float]] = [
    {
        "crop_en": "Tomato",
        "crop_te": "\u0c1f\u0c2e\u0c3e\u0c1f\u0c3e",
        "mandi": "Bowenpally Market Yard",
        "mandal": "Balanagar",
        "district": "Medchal-Malkajgiri",
        "min": 1200.0,
        "max": 2100.0,
        "modal": 1650.0,
    },
    {
        "crop_en": "Onion",
        "crop_te": "\u0c09\u0c32\u0c4d\u0c32\u0c3f\u0c2a\u0c3e\u0c2f",
        "mandi": "Malakpet Market Yard",
        "mandal": "Malakpet",
        "district": "Hyderabad",
        "min": 1500.0,
        "max": 2600.0,
        "modal": 2050.0,
    },
    {
        "crop_en": "Paddy (Common)",
        "crop_te": "\u0c35\u0c30\u0c3f",
        "mandi": "Karimnagar Agricultural Market",
        "mandal": "Karimnagar",
        "district": "Karimnagar",
        "min": 1980.0,
        "max": 2270.0,
        "modal": 2183.0,
    },
    {
        "crop_en": "Maize",
        "crop_te": "\u0c2e\u0c15\u0c4d\u0c15\u0c1c\u0c4a\u0c28\u0c4d\u0c28",
        "mandi": "Nizamabad Market Yard",
        "mandal": "Nizamabad",
        "district": "Nizamabad",
        "min": 1850.0,
        "max": 2180.0,
        "modal": 2020.0,
    },
    {
        "crop_en": "Cotton",
        "crop_te": "\u0c2a\u0c4a\u0c17\u0c3e\u0c15\u0c41",
        "mandi": "Warangal Enumamula Market",
        "mandal": "Warangal",
        "district": "Warangal",
        "min": 6800.0,
        "max": 7550.0,
        "modal": 7121.0,
    },
    {
        "crop_en": "Red Gram (Tur)",
        "crop_te": "\u0c15\u0c02\u0c26\u0c41\u0c32\u0c41",
        "mandi": "Tandur Market Yard",
        "mandal": "Tandur",
        "district": "Vikarabad",
        "min": 6900.0,
        "max": 8100.0,
        "modal": 7400.0,
    },
    {
        "crop_en": "Green Chilli",
        "crop_te": "\u0c2a\u0c1a\u0c4d\u0c1a\u0c3f\u0c2e\u0c3f\u0c30\u0c2a\u0c15\u0c3e\u0c2f\u0c32\u0c41",
        "mandi": "Khammam Agricultural Market",
        "mandal": "Khammam",
        "district": "Khammam",
        "min": 2600.0,
        "max": 4200.0,
        "modal": 3300.0,
    },
    {
        "crop_en": "Turmeric",
        "crop_te": "\u0c2a\u0c38\u0c41\u0c2a\u0c41",
        "mandi": "Nizamabad Turmeric Market",
        "mandal": "Nizamabad",
        "district": "Nizamabad",
        "min": 12500.0,
        "max": 16800.0,
        "modal": 14600.0,
    },
    {
        "crop_en": "Brinjal",
        "crop_te": "\u0c35\u0c02\u0c15\u0c3e\u0c2f",
        "mandi": "Gudimalkapur Market Yard",
        "mandal": "Mehdipatnam",
        "district": "Hyderabad",
        "min": 900.0,
        "max": 1700.0,
        "modal": 1280.0,
    },
    {
        "crop_en": "Groundnut",
        "crop_te": "\u0c35\u0c47\u0c30\u0c41\u0c36\u0c28\u0c17",
        "mandi": "Mahabubnagar Market Yard",
        "mandal": "Mahabubnagar",
        "district": "Mahabubnagar",
        "min": 5200.0,
        "max": 6400.0,
        "modal": 5800.0,
    },
]

MANDI_SOURCE_NAME = (
    "Telangana Agricultural Marketing Department / Agmarknet reference band"
)
MANDI_SOURCE_URL = "https://agmarknet.gov.in/"


# ----------------------------------------------------------------- advisory
ADVISORY_ROWS: list[dict[str, str]] = [
    {
        "slug": "tomato-fruit-borer-management",
        "crop_en": "Tomato",
        "crop_te": "\u0c1f\u0c2e\u0c3e\u0c1f\u0c3e",
        "topic": "pest",
        "season": "kharif",
        "source_type": "icar",
        "source_name": "ICAR - Indian Institute of Horticultural Research",
        "source_url": "https://iihr.res.in/",
        "title_en": "Managing tomato fruit borer without over-spraying",
        "title_te": (
            "\u0c1f\u0c2e\u0c3e\u0c1f\u0c3e \u0c15\u0c3e\u0c2f\u0c24\u0c4a\u0c32\u0c3f\u0c1a\u0c47 "
            "\u0c2a\u0c41\u0c30\u0c41\u0c17\u0c41 \u0c28\u0c3f\u0c30\u0c4d\u0c35\u0c39\u0c23"
        ),
        "summary_en": (
            "Scout twice a week, install 5 pheromone traps per acre and pick "
            "infested fruits before resorting to any chemical spray."
        ),
        "summary_te": (
            "\u0c35\u0c3e\u0c30\u0c3e\u0c28\u0c3f\u0c15\u0c3f \u0c30\u0c46\u0c02\u0c21\u0c41 "
            "\u0c38\u0c3e\u0c30\u0c4d\u0c32\u0c41 \u0c2a\u0c30\u0c3f\u0c36\u0c40\u0c32\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f, "
            "\u0c0e\u0c15\u0c30\u0c3e\u0c28\u0c3f\u0c15\u0c3f 5 \u0c2b\u0c46\u0c30\u0c4b\u0c2e\u0c4b\u0c28\u0c4d "
            "\u0c1f\u0c4d\u0c30\u0c3e\u0c2a\u0c4d\u0c32\u0c41 \u0c2a\u0c46\u0c1f\u0c4d\u0c1f\u0c02\u0c21\u0c3f."
        ),
        "body_en": (
            "1. Scout 20 random plants twice a week and record bored fruits.\n"
            "2. Install 5 pheromone traps per acre with Helicoverpa lures and "
            "replace lures every 21 days.\n"
            "3. Hand-pick and destroy bored fruits; do not leave them on bunds.\n"
            "4. Encourage natural enemies by keeping a marigold border row.\n"
            "5. Spray only when trap catches cross 8 moths per trap per week, "
            "and rotate approved molecules between sprays.\n"
            "Observe the label waiting period before harvesting for sale."
        ),
        "body_te": (
            "1. \u0c35\u0c3e\u0c30\u0c3e\u0c28\u0c3f\u0c15\u0c3f \u0c30\u0c46\u0c02\u0c21\u0c41 "
            "\u0c38\u0c3e\u0c30\u0c4d\u0c32\u0c41 20 \u0c2e\u0c4a\u0c15\u0c4d\u0c15\u0c32\u0c28\u0c41 "
            "\u0c2a\u0c30\u0c3f\u0c36\u0c40\u0c32\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "2. \u0c0e\u0c15\u0c30\u0c3e\u0c28\u0c3f\u0c15\u0c3f 5 \u0c2b\u0c46\u0c30\u0c4b\u0c2e\u0c4b\u0c28\u0c4d "
            "\u0c1f\u0c4d\u0c30\u0c3e\u0c2a\u0c4d\u0c32\u0c41 \u0c05\u0c2e\u0c30\u0c4d\u0c1a\u0c02\u0c21\u0c3f.\n"
            "3. \u0c2a\u0c41\u0c30\u0c41\u0c17\u0c41 \u0c38\u0c4b\u0c15\u0c3f\u0c28 "
            "\u0c15\u0c3e\u0c2f\u0c32\u0c28\u0c41 \u0c1a\u0c47\u0c24\u0c4b "
            "\u0c24\u0c40\u0c38\u0c3f \u0c28\u0c3e\u0c36\u0c28\u0c02 \u0c1a\u0c47\u0c2f\u0c02\u0c21\u0c3f.\n"
            "4. \u0c2e\u0c02\u0c26\u0c41 \u0c2a\u0c3f\u0c1a\u0c3f\u0c15\u0c3e\u0c30\u0c3f "
            "\u0c1a\u0c47\u0c38\u0c47 \u0c2e\u0c41\u0c02\u0c26\u0c41 "
            "\u0c38\u0c42\u0c1a\u0c3f\u0c15\u0c32\u0c28\u0c41 \u0c2a\u0c3e\u0c1f\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f."
        ),
    },
    {
        "slug": "paddy-water-management-rabi",
        "crop_en": "Paddy (Common)",
        "crop_te": "\u0c35\u0c30\u0c3f",
        "topic": "irrigation",
        "season": "rabi",
        "source_type": "icar",
        "source_name": "ICAR - Indian Institute of Rice Research, Hyderabad",
        "source_url": "https://icar-iirr.org/",
        "title_en": "Alternate wetting and drying for rabi paddy",
        "title_te": (
            "\u0c30\u0c2c\u0c40 \u0c35\u0c30\u0c3f\u0c15\u0c3f "
            "\u0c2e\u0c3e\u0c30\u0c4d\u0c1a\u0c3f\u0c2e\u0c3e\u0c30\u0c4d\u0c1a\u0c3f "
            "\u0c28\u0c40\u0c1f\u0c3f \u0c2f\u0c3e\u0c1c\u0c2e\u0c3e\u0c28\u0c4d\u0c2f\u0c02"
        ),
        "summary_en": (
            "Irrigate 2-3 cm one day after the ponded water disappears; this "
            "saves roughly 25% water without yield loss."
        ),
        "summary_te": (
            "\u0c28\u0c40\u0c30\u0c41 \u0c2e\u0c3e\u0c2f\u0c2e\u0c46\u0c56\u0c28 "
            "\u0c2e\u0c30\u0c41\u0c38\u0c1f\u0c3f \u0c30\u0c4b\u0c1c\u0c41 2-3 "
            "\u0c38\u0c46.\u0c2e\u0c40. \u0c28\u0c40\u0c30\u0c41 \u0c2a\u0c46\u0c1f\u0c4d\u0c1f\u0c02\u0c21\u0c3f."
        ),
        "body_en": (
            "Keep the field saturated for the first 15 days after transplanting.\n"
            "Then follow alternate wetting and drying: apply 2-3 cm of water one "
            "day after the ponded water disappears from the surface.\n"
            "Maintain a thin water layer during panicle initiation and flowering, "
            "the two stages that must never face stress.\n"
            "Drain the field 10 days before harvest so grain moisture settles and "
            "the crop can be lifted cleanly."
        ),
        "body_te": (
            "\u0c28\u0c3e\u0c1f\u0c3f\u0c28 \u0c24\u0c30\u0c4d\u0c35\u0c3e\u0c24 "
            "\u0c2e\u0c4a\u0c26\u0c1f\u0c3f 15 \u0c30\u0c4b\u0c1c\u0c41\u0c32\u0c41 "
            "\u0c2a\u0c4a\u0c32\u0c02 \u0c24\u0c47\u0c2e\u0c17\u0c3e "
            "\u0c09\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "\u0c24\u0c30\u0c41\u0c35\u0c3e\u0c24 \u0c2e\u0c3e\u0c30\u0c4d\u0c1a\u0c3f "
            "\u0c2e\u0c3e\u0c30\u0c4d\u0c1a\u0c3f \u0c24\u0c21\u0c3f-\u0c06\u0c30\u0c41 "
            "\u0c2a\u0c26\u0c4d\u0c26\u0c24\u0c3f \u0c2a\u0c3e\u0c1f\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "\u0c15\u0c4b\u0c24 \u0c15\u0c4b\u0c2f\u0c21\u0c3e\u0c28\u0c3f\u0c15\u0c3f 10 "
            "\u0c30\u0c4b\u0c1c\u0c41\u0c32 \u0c2e\u0c41\u0c02\u0c26\u0c41 "
            "\u0c28\u0c40\u0c30\u0c41 \u0c24\u0c40\u0c38\u0c3f\u0c35\u0c47\u0c2f\u0c02\u0c21\u0c3f."
        ),
    },
    {
        "slug": "cotton-pink-bollworm-kvk",
        "crop_en": "Cotton",
        "crop_te": "\u0c2a\u0c4a\u0c17\u0c3e\u0c15\u0c41",
        "topic": "pest",
        "season": "kharif",
        "source_type": "kvk",
        "source_name": "Krishi Vigyan Kendra, Warangal",
        "source_url": "https://kvk.icar.gov.in/",
        "title_en": "Pink bollworm: timely termination beats extra sprays",
        "title_te": (
            "\u0c17\u0c41\u0c32\u0c3e\u0c2c\u0c40 \u0c15\u0c3e\u0c2f\u0c24\u0c4a\u0c32\u0c3f\u0c1a\u0c47 "
            "\u0c2a\u0c41\u0c30\u0c41\u0c17\u0c41: \u0c38\u0c2e\u0c2f\u0c02\u0c32\u0c4b "
            "\u0c2a\u0c02\u0c1f \u0c2e\u0c41\u0c17\u0c3f\u0c02\u0c2a\u0c41"
        ),
        "summary_en": (
            "Install 8 pheromone traps per acre, remove rosette flowers weekly "
            "and terminate the crop by mid-January to break the pest cycle."
        ),
        "summary_te": (
            "\u0c0e\u0c15\u0c30\u0c3e\u0c28\u0c3f\u0c15\u0c3f 8 "
            "\u0c2b\u0c46\u0c30\u0c4b\u0c2e\u0c4b\u0c28\u0c4d \u0c1f\u0c4d\u0c30\u0c3e\u0c2a\u0c4d\u0c32\u0c41, "
            "\u0c1c\u0c28\u0c35\u0c30\u0c3f \u0c2e\u0c3e\u0c38\u0c3e\u0c02\u0c24\u0c02\u0c32\u0c4b "
            "\u0c2a\u0c02\u0c1f \u0c2e\u0c41\u0c17\u0c3f\u0c02\u0c2a\u0c41."
        ),
        "body_en": (
            "Use pheromone traps at 8 per acre from 45 days after sowing and "
            "record weekly catches.\n"
            "Remove and destroy rosette (twisted) flowers every week, since each "
            "one shelters larvae.\n"
            "Avoid extending the crop beyond mid-January; carry-over bolls are "
            "the main source of next season's infestation.\n"
            "Shred and incorporate stalks immediately after the final pick."
        ),
        "body_te": (
            "\u0c35\u0c3f\u0c24\u0c4d\u0c24\u0c3f\u0c28 45 \u0c30\u0c4b\u0c1c\u0c41\u0c32 "
            "\u0c24\u0c30\u0c41\u0c35\u0c3e\u0c24 \u0c1f\u0c4d\u0c30\u0c3e\u0c2a\u0c4d\u0c32\u0c41 "
            "\u0c05\u0c2e\u0c30\u0c4d\u0c1a\u0c02\u0c21\u0c3f.\n"
            "\u0c2e\u0c46\u0c32\u0c3f\u0c15\u0c3f\u0c28 \u0c2a\u0c42\u0c32\u0c28\u0c41 "
            "\u0c2a\u0c4d\u0c30\u0c24\u0c3f \u0c35\u0c3e\u0c30\u0c02 "
            "\u0c24\u0c4a\u0c32\u0c17\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "\u0c1c\u0c28\u0c35\u0c30\u0c3f \u0c2e\u0c3e\u0c38\u0c3e\u0c02\u0c24\u0c02 "
            "\u0c26\u0c3e\u0c1f\u0c3f \u0c2a\u0c02\u0c1f\u0c28\u0c41 "
            "\u0c15\u0c4a\u0c28\u0c38\u0c3e\u0c17\u0c3f\u0c02\u0c1a\u0c35\u0c26\u0c4d\u0c26\u0c41."
        ),
    },
    {
        "slug": "turmeric-boiling-and-drying",
        "crop_en": "Turmeric",
        "crop_te": "\u0c2a\u0c38\u0c41\u0c2a\u0c41",
        "topic": "post_harvest",
        "season": "rabi",
        "source_type": "icar",
        "source_name": "ICAR - Indian Institute of Spices Research",
        "source_url": "https://www.spices.res.in/",
        "title_en": "Curing turmeric for better colour and price",
        "title_te": (
            "\u0c2e\u0c02\u0c1a\u0c3f \u0c30\u0c02\u0c17\u0c41, \u0c27\u0c30 "
            "\u0c15\u0c4b\u0c38\u0c02 \u0c2a\u0c38\u0c41\u0c2a\u0c41 "
            "\u0c15\u0c4d\u0c2f\u0c42\u0c30\u0c3f\u0c02\u0c17\u0c4d"
        ),
        "summary_en": (
            "Boil rhizomes within 3 days of harvest for 45-60 minutes, then "
            "sun-dry to 8-10% moisture for a uniform, saleable colour."
        ),
        "summary_te": (
            "\u0c15\u0c4b\u0c24 \u0c24\u0c30\u0c4d\u0c35\u0c3e\u0c24 3 "
            "\u0c30\u0c4b\u0c1c\u0c41\u0c32\u0c32\u0c4b 45-60 "
            "\u0c28\u0c3f\u0c2e\u0c3f\u0c37\u0c3e\u0c32\u0c41 \u0c09\u0c26\u0c3f\u0c15\u0c3f\u0c02\u0c1a\u0c3f "
            "\u0c0e\u0c02\u0c21\u0c2c\u0c46\u0c1f\u0c4d\u0c1f\u0c02\u0c21\u0c3f."
        ),
        "body_en": (
            "Separate mother rhizomes from fingers and cure them in different "
            "batches.\n"
            "Boil in just enough water to cover the rhizomes for 45-60 minutes, "
            "until froth appears and a white smoke with typical aroma is given "
            "off.\n"
            "Spread in 5-7 cm layers on a clean floor and sun-dry for 10-15 days "
            "to 8-10% moisture.\n"
            "Polish and grade before listing; graded lots fetch a better price."
        ),
        "body_te": (
            "\u0c24\u0c32\u0c4d\u0c32\u0c3f \u0c15\u0c4a\u0c2e\u0c4d\u0c2e\u0c41\u0c32\u0c28\u0c41, "
            "\u0c2a\u0c3f\u0c32\u0c4d\u0c32 \u0c15\u0c4a\u0c2e\u0c4d\u0c2e\u0c41\u0c32\u0c28\u0c41 "
            "\u0c35\u0c47\u0c30\u0c41 \u0c1a\u0c47\u0c2f\u0c02\u0c21\u0c3f.\n"
            "\u0c2e\u0c41\u0c28\u0c3f\u0c17\u0c47 \u0c28\u0c40\u0c1f\u0c3f\u0c32\u0c4b "
            "45-60 \u0c28\u0c3f\u0c2e\u0c3f\u0c37\u0c3e\u0c32\u0c41 "
            "\u0c09\u0c26\u0c3f\u0c15\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "10-15 \u0c30\u0c4b\u0c1c\u0c41\u0c32\u0c41 \u0c0e\u0c02\u0c21\u0c32\u0c4b "
            "\u0c06\u0c30\u0c2c\u0c46\u0c1f\u0c4d\u0c1f\u0c02\u0c21\u0c3f."
        ),
    },
    {
        "slug": "onion-storage-losses",
        "crop_en": "Onion",
        "crop_te": "\u0c09\u0c32\u0c4d\u0c32\u0c3f\u0c2a\u0c3e\u0c2f",
        "topic": "post_harvest",
        "season": "all_year",
        "source_type": "icar",
        "source_name": "ICAR - Directorate of Onion and Garlic Research",
        "source_url": "https://dogr.icar.gov.in/",
        "title_en": "Cutting onion storage losses on the farm",
        "title_te": (
            "\u0c09\u0c32\u0c4d\u0c32\u0c3f\u0c2a\u0c3e\u0c2f "
            "\u0c28\u0c3f\u0c32\u0c4d\u0c35 \u0c28\u0c37\u0c4d\u0c1f\u0c3e\u0c32\u0c28\u0c41 "
            "\u0c24\u0c17\u0c4d\u0c17\u0c3f\u0c02\u0c1a\u0c21\u0c02"
        ),
        "summary_en": (
            "Stop irrigation 15 days before harvest, cure bulbs in shade for "
            "3-4 days and store in ventilated 30 cm layers."
        ),
        "summary_te": (
            "\u0c15\u0c4b\u0c24\u0c15\u0c41 15 \u0c30\u0c4b\u0c1c\u0c41\u0c32 "
            "\u0c2e\u0c41\u0c02\u0c26\u0c41 \u0c28\u0c40\u0c1f\u0c3f "
            "\u0c24\u0c21\u0c3f \u0c06\u0c2a\u0c02\u0c21\u0c3f, "
            "\u0c28\u0c40\u0c1f\u0c3f\u0c32\u0c4b \u0c15\u0c3e\u0c26\u0c41 "
            "\u0c28\u0c40\u0c21\u0c32\u0c4b \u0c15\u0c4d\u0c2f\u0c42\u0c30\u0c4d "
            "\u0c1a\u0c47\u0c2f\u0c02\u0c21\u0c3f."
        ),
        "body_en": (
            "Withhold irrigation 15 days before harvest so necks dry down.\n"
            "Harvest when 50-70% of the tops fall over, then field-cure with tops "
            "covering the bulbs for 3-4 days in shade.\n"
            "Cut tops 2 cm above the bulb, remove doubles and sprouted bulbs.\n"
            "Store in ventilated structures in layers no deeper than 30 cm; "
            "inspect fortnightly and remove rotting bulbs at once."
        ),
        "body_te": (
            "\u0c15\u0c4b\u0c24\u0c15\u0c41 15 \u0c30\u0c4b\u0c1c\u0c41\u0c32 "
            "\u0c2e\u0c41\u0c02\u0c26\u0c41 \u0c28\u0c40\u0c30\u0c41 "
            "\u0c2a\u0c46\u0c1f\u0c4d\u0c1f\u0c15\u0c02\u0c21\u0c3f.\n"
            "50-70% \u0c2e\u0c4a\u0c15\u0c4d\u0c15\u0c32\u0c41 \u0c35\u0c3e\u0c32\u0c3f\u0c28 "
            "\u0c24\u0c30\u0c41\u0c35\u0c3e\u0c24 \u0c15\u0c4b\u0c2f\u0c02\u0c21\u0c3f.\n"
            "30 \u0c38\u0c46.\u0c2e\u0c40. \u0c2a\u0c4a\u0c30\u0c32\u0c15\u0c02\u0c1f\u0c47 "
            "\u0c0e\u0c15\u0c4d\u0c15\u0c41\u0c35 \u0c2a\u0c4b\u0c38\u0c3f "
            "\u0c28\u0c3f\u0c32\u0c4d\u0c35 \u0c1a\u0c47\u0c2f\u0c15\u0c02\u0c21\u0c3f."
        ),
    },
    {
        "slug": "red-gram-soil-health-kvk",
        "crop_en": "Red Gram (Tur)",
        "crop_te": "\u0c15\u0c02\u0c26\u0c41\u0c32\u0c41",
        "topic": "soil_health",
        "season": "kharif",
        "source_type": "kvk",
        "source_name": "Krishi Vigyan Kendra, Vikarabad",
        "source_url": "https://kvk.icar.gov.in/",
        "title_en": "Soil test based nutrition for red gram",
        "title_te": (
            "\u0c15\u0c02\u0c26\u0c41\u0c32\u0c15\u0c41 \u0c2e\u0c1f\u0c4d\u0c1f\u0c3f "
            "\u0c2a\u0c30\u0c40\u0c15\u0c4d\u0c37 \u0c06\u0c27\u0c3e\u0c30\u0c3f\u0c24 "
            "\u0c2a\u0c4b\u0c37\u0c15\u0c3e\u0c32\u0c41"
        ),
        "summary_en": (
            "Use a soil health card, treat seed with Rhizobium and apply "
            "phosphorus at sowing rather than later top dressing."
        ),
        "summary_te": (
            "\u0c2e\u0c1f\u0c4d\u0c1f\u0c3f \u0c06\u0c30\u0c4b\u0c17\u0c4d\u0c2f "
            "\u0c15\u0c3e\u0c30\u0c4d\u0c21\u0c41 \u0c2a\u0c4d\u0c30\u0c15\u0c3e\u0c30\u0c02 "
            "\u0c2a\u0c4b\u0c37\u0c15\u0c3e\u0c32\u0c41 \u0c35\u0c3e\u0c26\u0c02\u0c21\u0c3f."
        ),
        "body_en": (
            "Collect a composite soil sample before the season and follow the "
            "soil health card recommendation.\n"
            "Treat seed with Rhizobium and PSB culture at 200 g per 10 kg seed.\n"
            "Apply the full phosphorus dose as basal at sowing; red gram responds "
            "poorly to late phosphorus.\n"
            "Nip the terminal buds at 45-50 days to encourage branching."
        ),
        "body_te": (
            "\u0c38\u0c40\u0c1c\u0c28\u0c4d \u0c2e\u0c41\u0c02\u0c26\u0c41 "
            "\u0c2e\u0c1f\u0c4d\u0c1f\u0c3f \u0c28\u0c2e\u0c42\u0c28\u0c3e "
            "\u0c2a\u0c30\u0c40\u0c15\u0c4d\u0c37 \u0c1a\u0c47\u0c2f\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "10 \u0c15\u0c3f\u0c32\u0c4b \u0c35\u0c3f\u0c24\u0c4d\u0c24\u0c28\u0c3e\u0c28\u0c3f\u0c15\u0c3f "
            "200 \u0c17\u0c4d\u0c30\u0c3e. \u0c30\u0c48\u0c1c\u0c4b\u0c2c\u0c3f\u0c2f\u0c02 "
            "\u0c2a\u0c1f\u0c4d\u0c1f\u0c3f\u0c02\u0c1a\u0c02\u0c21\u0c3f.\n"
            "45-50 \u0c30\u0c4b\u0c1c\u0c41\u0c32\u0c15\u0c41 \u0c15\u0c4a\u0c28\u0c32\u0c41 "
            "\u0c17\u0c3f\u0c32\u0c4d\u0c32\u0c02\u0c1a\u0c02\u0c21\u0c3f."
        ),
    },
]

ADVISORY_DISCLAIMER_EN = (
    "General guidance summarised from the cited public source. Confirm doses "
    "and timing with your local Agriculture Extension Officer or KVK before "
    "acting, and always follow product label instructions."
)
ADVISORY_DISCLAIMER_TE = (
    "\u0c2a\u0c48 \u0c38\u0c42\u0c1a\u0c28\u0c32\u0c41 \u0c38\u0c3e\u0c27\u0c3e\u0c30\u0c23 "
    "\u0c2e\u0c3e\u0c30\u0c4d\u0c17\u0c26\u0c30\u0c4d\u0c36\u0c15\u0c02 \u0c2e\u0c3e\u0c24\u0c4d\u0c30\u0c2e\u0c47. "
    "\u0c2e\u0c40 \u0c38\u0c4d\u0c25\u0c3e\u0c28\u0c3f\u0c15 \u0c35\u0c4d\u0c2f\u0c35\u0c38\u0c3e\u0c2f "
    "\u0c05\u0c27\u0c3f\u0c15\u0c3e\u0c30\u0c3f \u0c32\u0c47\u0c26\u0c3e KVK "
    "\u0c38\u0c32\u0c39\u0c3e \u0c24\u0c40\u0c38\u0c41\u0c15\u0c4b\u0c02\u0c21\u0c3f."
)


# ------------------------------------------------------------- demo farmers
DEMO_FARMERS: list[dict[str, str | float | int]] = [
    {
        "email": f"demo.farmer.sarita@{DEMO_EMAIL_DOMAIN}",
        "name_en": "Sarita Devi (Demo)",
        "name_te": "\u0c38\u0c30\u0c3f\u0c24 \u0c26\u0c47\u0c35\u0c3f",
        "bio_en": (
            "Demo record: two-acre vegetable plot near Shamirpet, growing "
            "tomato and brinjal for nearby households."
        ),
        "bio_te": (
            "\u0c37\u0c2e\u0c3f\u0c30\u0c4d\u0c2a\u0c47\u0c1f\u0c4d "
            "\u0c38\u0c2e\u0c40\u0c2a\u0c02\u0c32\u0c4b \u0c30\u0c46\u0c02\u0c21\u0c41 "
            "\u0c0e\u0c15\u0c30\u0c3e\u0c32 \u0c15\u0c42\u0c30\u0c17\u0c24\u0c4b\u0c1f."
        ),
        "years": 12,
        "crops": "Tomato, Brinjal",
        "farm_name": "Shamirpet Kitchen Garden (Demo)",
        "village": "Shamirpet",
        "mandal": "Shamirpet",
        "district": "Medchal-Malkajgiri",
        "pincode": "500078",
        "lat": 17.6011,
        "lon": 78.5691,
        "acres": 2.0,
        "mandi": "Bowenpally Market Yard",
    },
    {
        "email": f"demo.farmer.ramulu@{DEMO_EMAIL_DOMAIN}",
        "name_en": "Ramulu Yadav (Demo)",
        "name_te": "\u0c30\u0c3e\u0c2e\u0c41\u0c32\u0c41 \u0c2f\u0c3e\u0c26\u0c35\u0c4d",
        "bio_en": (
            "Demo record: paddy and maize grower on the Karimnagar canal, "
            "selling graded lots directly to buyers."
        ),
        "bio_te": (
            "\u0c15\u0c30\u0c40\u0c02\u0c28\u0c17\u0c30\u0c4d "
            "\u0c15\u0c3e\u0c32\u0c4d\u0c35\u0c3e \u0c2a\u0c30\u0c3f\u0c35\u0c3e\u0c39\u0c15 "
            "\u0c2a\u0c4d\u0c30\u0c3e\u0c02\u0c24\u0c02\u0c32\u0c4b \u0c35\u0c30\u0c3f "
            "\u0c38\u0c3e\u0c17\u0c41."
        ),
        "years": 20,
        "crops": "Paddy, Maize",
        "farm_name": "Manair Canal Field (Demo)",
        "village": "Manakondur",
        "mandal": "Manakondur",
        "district": "Karimnagar",
        "pincode": "505469",
        "lat": 18.3421,
        "lon": 79.1601,
        "acres": 6.5,
        "mandi": "Karimnagar Agricultural Market",
    },
    {
        "email": f"demo.farmer.lakshmi@{DEMO_EMAIL_DOMAIN}",
        "name_en": "Lakshmi Bai (Demo)",
        "name_te": "\u0c32\u0c15\u0c4d\u0c37\u0c4d\u0c2e\u0c3f \u0c2c\u0c3e\u0c2f\u0c3f",
        "bio_en": (
            "Demo record: turmeric and chilli grower near Nizamabad, curing "
            "and grading on the farm before listing."
        ),
        "bio_te": (
            "\u0c28\u0c3f\u0c1c\u0c3e\u0c2e\u0c3e\u0c2c\u0c3e\u0c26\u0c4d "
            "\u0c38\u0c2e\u0c40\u0c2a\u0c02\u0c32\u0c4b \u0c2a\u0c38\u0c41\u0c2a\u0c41, "
            "\u0c2e\u0c3f\u0c30\u0c2a \u0c38\u0c3e\u0c17\u0c41."
        ),
        "years": 15,
        "crops": "Turmeric, Green Chilli",
        "farm_name": "Nizamabad Turmeric Plot (Demo)",
        "village": "Dichpally",
        "mandal": "Dichpally",
        "district": "Nizamabad",
        "pincode": "503175",
        "lat": 18.5556,
        "lon": 78.1230,
        "acres": 4.0,
        "mandi": "Nizamabad Turmeric Market",
    },
]

DEMO_LISTINGS: list[dict[str, str | float]] = [
    {
        "farmer_email": DEMO_FARMERS[0]["email"],
        "crop_en": "Tomato",
        "crop_te": "\u0c1f\u0c2e\u0c3e\u0c1f\u0c3e",
        "variety": "Hybrid Sahoo",
        "grade": "A",
        "desc_en": (
            "Demo listing: firm, field-picked tomatoes suitable for household "
            "and small hotel buyers."
        ),
        "desc_te": (
            "\u0c24\u0c3e\u0c1c\u0c3e\u0c17\u0c3e \u0c15\u0c4b\u0c38\u0c3f\u0c28 "
            "\u0c17\u0c1f\u0c4d\u0c1f\u0c3f \u0c1f\u0c2e\u0c3e\u0c1f\u0c3e\u0c32\u0c41."
        ),
        "qty": 320.0,
        "unit": "kg",
        "price": 22.0,
        "harvest_offset_days": 0,
        "delivery": True,
        "radius": 15.0,
    },
    {
        "farmer_email": DEMO_FARMERS[1]["email"],
        "crop_en": "Paddy (Common)",
        "crop_te": "\u0c35\u0c30\u0c3f",
        "variety": "MTU-1010",
        "grade": "Fair Average Quality",
        "desc_en": (
            "Demo listing: cleaned and dried paddy, moisture around 13%, "
            "available in 50 kg bags."
        ),
        "desc_te": (
            "\u0c36\u0c41\u0c26\u0c4d\u0c26\u0c3f \u0c1a\u0c47\u0c38\u0c3f "
            "\u0c0e\u0c02\u0c21\u0c2c\u0c46\u0c1f\u0c4d\u0c1f\u0c3f\u0c28 "
            "\u0c35\u0c30\u0c3f."
        ),
        "qty": 40.0,
        "unit": "quintal",
        "price": 2240.0,
        "harvest_offset_days": 3,
        "delivery": False,
        "radius": 0.0,
    },
    {
        "farmer_email": DEMO_FARMERS[2]["email"],
        "crop_en": "Turmeric",
        "crop_te": "\u0c2a\u0c38\u0c41\u0c2a\u0c41",
        "variety": "Armoor Local",
        "grade": "Polished Finger",
        "desc_en": (
            "Demo listing: farm-cured and polished turmeric fingers, graded "
            "and bagged on the farm."
        ),
        "desc_te": (
            "\u0c2a\u0c4a\u0c32\u0c02\u0c32\u0c4b\u0c28\u0c47 "
            "\u0c15\u0c4d\u0c2f\u0c42\u0c30\u0c4d \u0c1a\u0c47\u0c38\u0c3f\u0c28 "
            "\u0c2a\u0c38\u0c41\u0c2a\u0c41 \u0c15\u0c4a\u0c2e\u0c4d\u0c2e\u0c41\u0c32\u0c41."
        ),
        "qty": 18.0,
        "unit": "quintal",
        "price": 15200.0,
        "harvest_offset_days": 1,
        "delivery": True,
        "radius": 30.0,
    },
]

_UNIT_MAP: dict[str, QuantityUnit] = {
    "kg": QuantityUnit.KG,
    "quintal": QuantityUnit.QUINTAL,
}


# ------------------------------------------------------------------ seeding


def _seed_mandi_prices(session: Session, price_date: dt.date) -> int:
    inserted = 0
    for row in MANDI_ROWS:
        crop_en = str(row["crop_en"])
        slug = slugify(crop_en)
        mandi_name = str(row["mandi"])
        exists = session.scalar(
            select(func.count())
            .select_from(MandiPrice)
            .where(
                MandiPrice.crop_slug == slug,
                MandiPrice.mandi_name == mandi_name,
                MandiPrice.price_date == price_date,
            )
        )
        if exists:
            continue
        session.add(
            MandiPrice(
                crop_name_en=crop_en,
                crop_name_te=str(row["crop_te"]),
                crop_slug=slug,
                mandi_name=mandi_name,
                mandal=str(row["mandal"]),
                district=str(row["district"]),
                unit=QuantityUnit.QUINTAL,
                min_price=float(row["min"]),
                max_price=float(row["max"]),
                modal_price=float(row["modal"]),
                price_date=price_date,
                source_name=MANDI_SOURCE_NAME,
                source_url=MANDI_SOURCE_URL,
            )
        )
        inserted += 1
    return inserted


def _seed_advisory(session: Session, reviewed_on: dt.date) -> int:
    inserted = 0
    for row in ADVISORY_ROWS:
        exists = session.scalar(
            select(func.count())
            .select_from(AdvisoryEntry)
            .where(AdvisoryEntry.slug == row["slug"])
        )
        if exists:
            continue
        session.add(
            AdvisoryEntry(
                slug=row["slug"],
                title_en=row["title_en"],
                title_te=row["title_te"],
                summary_en=row["summary_en"],
                summary_te=row["summary_te"],
                body_en=row["body_en"],
                body_te=row["body_te"],
                crop_name_en=row["crop_en"],
                crop_name_te=row["crop_te"],
                crop_slug=slugify(row["crop_en"]),
                topic=row["topic"],
                season=AdvisorySeason(row["season"]),
                source_type=AdvisorySource(row["source_type"]),
                source_name=row["source_name"],
                source_url=row["source_url"],
                reviewed_on=reviewed_on,
                reviewed_by="Platform agronomy review",
                disclaimer_en=ADVISORY_DISCLAIMER_EN,
                disclaimer_te=ADVISORY_DISCLAIMER_TE,
                is_published=True,
            )
        )
        inserted += 1
    return inserted


def _demo_farmer_profile(
    session: Session, row: dict[str, str | float | int]
) -> FarmerProfile:
    email = str(row["email"])
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            # Random secret, immediately discarded: sign-in is impossible.
            password_hash=generate_unusable_password(),
            full_name=str(row["name_en"]),
            full_name_te=str(row["name_te"]),
            role=UserRole.FARMER,
            language_pref=LanguagePref.TE,
            default_village=str(row["village"]),
            default_mandal=str(row["mandal"]),
            default_district=str(row["district"]),
            default_pincode=str(row["pincode"]),
            default_latitude=float(row["lat"]),
            default_longitude=float(row["lon"]),
        )
        session.add(user)
        session.flush()

    profile = session.scalar(
        select(FarmerProfile).where(FarmerProfile.user_id == user.id)
    )
    if profile is None:
        profile = FarmerProfile(
            user_id=user.id,
            display_name=str(row["name_en"]),
            display_name_te=str(row["name_te"]),
            bio_en=str(row["bio_en"]),
            bio_te=str(row["bio_te"]),
            years_farming=int(row["years"]),
            primary_crops=str(row["crops"]),
            verification_status=VerificationStatus.VERIFIED,
            verification_note=f"{DEMO_TAG} {DEMO_NOTE_EN}",
            verified_at=dt.datetime.now(dt.timezone.utc),
            is_local_partner=True,
            local_partner_since=dt.date.today(),
        )
        session.add(profile)
        session.flush()

    farm = session.scalar(
        select(Farm).where(
            Farm.farmer_id == profile.id, Farm.name == str(row["farm_name"])
        )
    )
    if farm is None:
        session.add(
            Farm(
                farmer_id=profile.id,
                name=str(row["farm_name"]),
                name_te=str(row["name_te"]),
                village=str(row["village"]),
                mandal=str(row["mandal"]),
                district=str(row["district"]),
                pincode=str(row["pincode"]),
                latitude=float(row["lat"]),
                longitude=float(row["lon"]),
                geocode_source="seed_manual",
                area_acres=float(row["acres"]),
                nearest_mandi_name=str(row["mandi"]),
            )
        )
        session.flush()

    if not session.scalar(
        select(func.count())
        .select_from(VoiceIntroduction)
        .where(VoiceIntroduction.farmer_id == profile.id)
    ):
        session.add(
            VoiceIntroduction(
                farmer_id=profile.id,
                file_name="",
                duration_seconds=0.0,
                language=LanguagePref.TE,
                transcript_en=f"{DEMO_TAG} Voice introduction not recorded yet.",
                transcript_te=DEMO_NOTE_TE,
                is_active=False,
            )
        )
    return profile


def _seed_demo_marketplace(session: Session, price_date: dt.date) -> int:
    """Demo farmers, farms, live listings and same-day photo proof."""
    profiles: dict[str, FarmerProfile] = {}
    for row in DEMO_FARMERS:
        profiles[str(row["email"])] = _demo_farmer_profile(session, row)

    mandi_by_slug: dict[str, tuple[str, float]] = {}
    for record in session.scalars(
        select(MandiPrice).where(MandiPrice.price_date == price_date)
    ):
        mandi_by_slug[record.crop_slug] = (
            record.mandi_name,
            float(record.modal_price),
        )

    inserted = 0
    now = dt.datetime.now(dt.timezone.utc)
    for row in DEMO_LISTINGS:
        profile = profiles[str(row["farmer_email"])]
        crop_en = str(row["crop_en"])
        slug = slugify(crop_en)
        exists = session.scalar(
            select(func.count())
            .select_from(CropListing)
            .where(
                CropListing.farmer_id == profile.id,
                CropListing.crop_slug == slug,
            )
        )
        if exists:
            continue

        unit = _UNIT_MAP.get(row["unit"], QuantityUnit.KG)
        mandi_name, modal = mandi_by_slug.get(slug, ("", 0.0))
        reference = None
        if modal:
            reference = (
                quintal_to_kg_price(modal) if unit is QuantityUnit.KG else modal
            )
        farm = session.scalar(
            select(Farm).where(Farm.farmer_id == profile.id).limit(1)
        )
        harvest = dt.date.today() - dt.timedelta(
            days=int(row["harvest_offset_days"])
        )
        listing = CropListing(
            farmer_id=profile.id,
            farm_id=farm.id if farm else None,
            crop_name_en=crop_en,
            crop_name_te=str(row["crop_te"]),
            crop_slug=slug,
            variety=str(row["variety"]),
            grade=str(row["grade"]),
            description_en=f"{DEMO_TAG} {row['desc_en']}",
            description_te=str(row["desc_te"]),
            quantity_total=float(row["qty"]),
            quantity_available=float(row["qty"]),
            unit=unit,
            min_order_quantity=1.0 if unit is QuantityUnit.KG else 1.0,
            price_per_unit=float(row["price"]),
            mandi_reference_price=reference,
            mandi_reference_name=mandi_name,
            harvest_date=harvest,
            listed_at=now,
            available_until=dt.date.today() + dt.timedelta(days=7),
            offers_delivery=bool(row["delivery"]),
            delivery_radius_km=float(row["radius"]),
            offers_pickup=True,
            status=ListingStatus.LIVE,
            has_same_day_proof=True,
        )
        session.add(listing)
        session.flush()

        session.add(
            CropPhotoProof(
                listing_id=listing.id,
                uploaded_by_id=None,
                file_name="placeholder.svg",
                mime_type="image/svg+xml",
                captured_at=now,
                capture_date=dt.date.today(),
                capture_source="seed_placeholder",
                is_same_day=True,
                is_primary=True,
                caption_en=f"{DEMO_TAG} Placeholder image for {crop_en}.",
                caption_te=DEMO_NOTE_TE,
                review_status=ProofReviewStatus.APPROVED,
                review_note=DEMO_NOTE_EN,
            )
        )
        inserted += 1
    return inserted


def seed_database(*, include_demo_marketplace: bool = True) -> dict[str, int]:
    """Insert starter data, skipping anything already present.

    Safe to call on every application start.
    """
    counts = {"mandi_prices": 0, "advisory_entries": 0, "demo_listings": 0}
    today = dt.date.today()
    try:
        with rx.session() as session:
            counts["mandi_prices"] = _seed_mandi_prices(session, today)
            counts["advisory_entries"] = _seed_advisory(session, today)
            session.commit()
            if include_demo_marketplace:
                counts["demo_listings"] = _seed_demo_marketplace(session, today)
                session.commit()
    except Exception as e:
        logging.exception(f"Error seeding starter data: {e}")
        return counts
    if any(counts.values()):
        logger.info(f"Seeded starter data: {counts}")
    return counts
