"""Managed-database model layer for the Telangana field-to-market marketplace.

Schema only: no queries, no UI. Every table carries timestamps, statuses and
bilingual (English / Telugu) fields needed by later experiences.
"""

from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class TimestampMixin(MappedAsDataclass, kw_only=True):
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=_utcnow,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ---------------------------------------------------------------- enumerations


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    FARMER = "farmer"
    ADMIN = "admin"


class LanguagePref(str, enum.Enum):
    EN = "en"
    TE = "te"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    LIVE = "live"
    RESERVED = "reserved"
    SOLD_OUT = "sold_out"
    UNPUBLISHED = "unpublished"
    EXPIRED = "expired"


class QuantityUnit(str, enum.Enum):
    KG = "kg"
    QUINTAL = "quintal"
    TONNE = "tonne"
    DOZEN = "dozen"
    BUNDLE = "bundle"
    CRATE = "crate"
    PIECE = "piece"


class ProofReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrderStatus(str, enum.Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    PAID = "paid"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class FulfilmentMode(str, enum.Enum):
    FARM_PICKUP = "farm_pickup"
    LOCAL_DELIVERY = "local_delivery"


class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    ATTEMPTED = "attempted"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    OTHER = "other"


class PayoutStatus(str, enum.Enum):
    DUE = "due"
    SCHEDULED = "scheduled"
    PAID = "paid"
    ON_HOLD = "on_hold"
    FAILED = "failed"


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED_BUYER = "resolved_buyer"
    RESOLVED_FARMER = "resolved_farmer"
    WITHDRAWN = "withdrawn"


class MessageKind(str, enum.Enum):
    TEXT = "text"
    VOICE_NOTE = "voice_note"
    SYSTEM = "system"


class AdvisorySource(str, enum.Enum):
    ICAR = "icar"
    KVK = "kvk"
    STATE_AGRI_DEPT = "state_agri_dept"
    OTHER = "other"


class AdvisorySeason(str, enum.Enum):
    KHARIF = "kharif"
    RABI = "rabi"
    ZAID = "zaid"
    ALL_YEAR = "all_year"


# ------------------------------------------------------------------- identity


class User(TimestampMixin, Base):
    """Email/password account. Passwords are stored only as a salted hash."""

    __tablename__ = "user_account"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        CheckConstraint(
            "position('@' in email) > 1", name="ck_user_email_shape"
        ),
        CheckConstraint(
            "char_length(password_hash) >= 20", name="ck_user_hash_len"
        ),
        Index("ix_user_role_active", "role", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    email: Mapped[str] = mapped_column(String(255), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    password_algo: Mapped[str] = mapped_column(
        String(32), default="pbkdf2_sha256"
    )
    password_updated_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    full_name: Mapped[str] = mapped_column(String(120), default="")
    full_name_te: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.CUSTOMER
    )
    language_pref: Mapped[LanguagePref] = mapped_column(
        Enum(LanguagePref, name="language_pref"), default=LanguagePref.EN
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_login_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    # Buyer-side location fallback when browser permission is denied.
    default_address_line: Mapped[str] = mapped_column(String(255), default="")
    default_village: Mapped[str] = mapped_column(String(120), default="")
    default_mandal: Mapped[str] = mapped_column(String(120), default="")
    default_district: Mapped[str] = mapped_column(String(120), default="")
    default_pincode: Mapped[str] = mapped_column(String(10), default="")
    default_latitude: Mapped[float | None] = mapped_column(Float, default=None)
    default_longitude: Mapped[float | None] = mapped_column(Float, default=None)

    farmer_profile: Mapped["FarmerProfile | None"] = relationship(
        back_populates="user",
        foreign_keys="FarmerProfile.user_id",
        uselist=False,
        init=False,
    )
    roles: Mapped[list["UserRoleAssignment"]] = relationship(
        back_populates="user",
        foreign_keys="UserRoleAssignment.user_id",
        init=False,
    )


class UserRoleAssignment(TimestampMixin, Base):
    """Extra role grants, so an account can act as both farmer and customer."""

    __tablename__ = "user_role_assignment"
    __table_args__ = (
        UniqueConstraint("user_id", "role", name="uq_user_role_once"),
        Index("ix_role_assignment_role", "role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"))
    granted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    note: Mapped[str] = mapped_column(String(255), default="")

    user: Mapped["User"] = relationship(
        back_populates="roles", foreign_keys=[user_id], init=False
    )


# --------------------------------------------------------- farmers and farms


class FarmerProfile(TimestampMixin, Base):
    """Farmer identity, verification and the local-partner badge."""

    __tablename__ = "farmer_profile"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_farmer_profile_user"),
        Index(
            "ix_farmer_verification", "verification_status", "is_local_partner"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"), index=True
    )
    display_name: Mapped[str] = mapped_column(String(120), default="")
    display_name_te: Mapped[str] = mapped_column(String(120), default="")
    bio_en: Mapped[str] = mapped_column(Text, default="")
    bio_te: Mapped[str] = mapped_column(Text, default="")
    years_farming: Mapped[int] = mapped_column(Integer, default=0)
    primary_crops: Mapped[str] = mapped_column(String(255), default="")
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.UNVERIFIED,
    )
    verification_note: Mapped[str] = mapped_column(Text, default="")
    verified_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    verified_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    id_document_ref: Mapped[str] = mapped_column(String(255), default="")
    is_local_partner: Mapped[bool] = mapped_column(Boolean, default=False)
    local_partner_since: Mapped[dt.date | None] = mapped_column(
        Date, default=None
    )
    payout_upi_id: Mapped[str] = mapped_column(String(120), default="")
    payout_account_name: Mapped[str] = mapped_column(String(120), default="")
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    completed_orders: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(
        back_populates="farmer_profile", foreign_keys=[user_id], init=False
    )
    farms: Mapped[list["Farm"]] = relationship(
        back_populates="farmer", init=False
    )
    listings: Mapped[list["CropListing"]] = relationship(
        back_populates="farmer", init=False
    )
    voice_intros: Mapped[list["VoiceIntroduction"]] = relationship(
        back_populates="farmer", init=False
    )


class Farm(TimestampMixin, Base):
    """A geocoded plot used for nearest-first discovery."""

    __tablename__ = "farm"
    __table_args__ = (
        CheckConstraint(
            "latitude is null or (latitude >= -90 and latitude <= 90)",
            name="ck_farm_lat_range",
        ),
        CheckConstraint(
            "longitude is null or (longitude >= -180 and longitude <= 180)",
            name="ck_farm_lon_range",
        ),
        Index("ix_farm_geo", "latitude", "longitude"),
        Index("ix_farm_district_mandal", "district", "mandal"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmer_profile.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), default="")
    name_te: Mapped[str] = mapped_column(String(120), default="")
    address_line: Mapped[str] = mapped_column(String(255), default="")
    village: Mapped[str] = mapped_column(String(120), default="")
    mandal: Mapped[str] = mapped_column(String(120), default="")
    district: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(80), default="Telangana")
    pincode: Mapped[str] = mapped_column(String(10), default="")
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    geocode_source: Mapped[str] = mapped_column(String(60), default="manual")
    geocode_accuracy_m: Mapped[float | None] = mapped_column(
        Float, default=None
    )
    area_acres: Mapped[float | None] = mapped_column(Float, default=None)
    nearest_mandi_name: Mapped[str] = mapped_column(String(120), default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    farmer: Mapped["FarmerProfile"] = relationship(
        back_populates="farms", init=False
    )
    listings: Mapped[list["CropListing"]] = relationship(
        back_populates="farm", init=False
    )


# ------------------------------------------------------------------- listings


class CropListing(TimestampMixin, Base):
    """A harvest offered to nearby buyers."""

    __tablename__ = "crop_listing"
    __table_args__ = (
        CheckConstraint(
            "quantity_available >= 0", name="ck_listing_qty_nonneg"
        ),
        CheckConstraint("price_per_unit > 0", name="ck_listing_price_positive"),
        Index("ix_listing_status_harvest", "status", "harvest_date"),
        Index("ix_listing_crop_slug", "crop_slug"),
        Index("ix_listing_farmer_status", "farmer_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmer_profile.id", ondelete="CASCADE"), index=True
    )
    farm_id: Mapped[int | None] = mapped_column(
        ForeignKey("farm.id", ondelete="SET NULL"), default=None, index=True
    )
    crop_name_en: Mapped[str] = mapped_column(String(120))
    crop_name_te: Mapped[str] = mapped_column(String(120), default="")
    crop_slug: Mapped[str] = mapped_column(String(120), default="")
    variety: Mapped[str] = mapped_column(String(120), default="")
    grade: Mapped[str] = mapped_column(String(40), default="")
    description_en: Mapped[str] = mapped_column(Text, default="")
    description_te: Mapped[str] = mapped_column(Text, default="")
    quantity_total: Mapped[float] = mapped_column(Float, default=0.0)
    quantity_available: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[QuantityUnit] = mapped_column(
        Enum(QuantityUnit, name="quantity_unit"), default=QuantityUnit.KG
    )
    min_order_quantity: Mapped[float] = mapped_column(Float, default=1.0)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    mandi_reference_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), default=None
    )
    mandi_reference_name: Mapped[str] = mapped_column(String(120), default="")
    harvest_date: Mapped[dt.date | None] = mapped_column(Date, default=None)
    listed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default_factory=_utcnow
    )
    available_until: Mapped[dt.date | None] = mapped_column(Date, default=None)
    offers_delivery: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_radius_km: Mapped[float] = mapped_column(Float, default=0.0)
    offers_pickup: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status"), default=ListingStatus.DRAFT
    )
    has_same_day_proof: Mapped[bool] = mapped_column(Boolean, default=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    interest_count: Mapped[int] = mapped_column(Integer, default=0)
    unpublished_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    farmer: Mapped["FarmerProfile"] = relationship(
        back_populates="listings", init=False
    )
    farm: Mapped["Farm | None"] = relationship(
        back_populates="listings", init=False
    )
    photo_proofs: Mapped[list["CropPhotoProof"]] = relationship(
        back_populates="listing", init=False
    )
    orders: Mapped[list["OrderRequest"]] = relationship(
        back_populates="listing", init=False
    )


class CropPhotoProof(TimestampMixin, Base):
    """Same-day photo evidence metadata for a listing."""

    __tablename__ = "crop_photo_proof"
    __table_args__ = (
        Index("ix_proof_listing_captured", "listing_id", "captured_at"),
        Index("ix_proof_review", "review_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("crop_listing.id", ondelete="CASCADE"), index=True
    )
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    file_name: Mapped[str] = mapped_column(String(255), default="")
    mime_type: Mapped[str] = mapped_column(String(80), default="image/jpeg")
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    width_px: Mapped[int] = mapped_column(Integer, default=0)
    height_px: Mapped[int] = mapped_column(Integer, default=0)
    captured_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    capture_date: Mapped[dt.date | None] = mapped_column(Date, default=None)
    capture_latitude: Mapped[float | None] = mapped_column(Float, default=None)
    capture_longitude: Mapped[float | None] = mapped_column(Float, default=None)
    capture_source: Mapped[str] = mapped_column(String(40), default="camera")
    is_same_day: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    caption_en: Mapped[str] = mapped_column(String(255), default="")
    caption_te: Mapped[str] = mapped_column(String(255), default="")
    review_status: Mapped[ProofReviewStatus] = mapped_column(
        Enum(ProofReviewStatus, name="proof_review_status"),
        default=ProofReviewStatus.PENDING,
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    review_note: Mapped[str] = mapped_column(Text, default="")

    listing: Mapped["CropListing"] = relationship(
        back_populates="photo_proofs", init=False
    )


class VoiceIntroduction(TimestampMixin, Base):
    """Short Telugu or English spoken introduction by a farmer."""

    __tablename__ = "voice_introduction"
    __table_args__ = (
        Index("ix_voice_farmer_active", "farmer_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmer_profile.id", ondelete="CASCADE"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), default="")
    mime_type: Mapped[str] = mapped_column(String(80), default="audio/webm")
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[LanguagePref] = mapped_column(
        Enum(LanguagePref, name="language_pref"), default=LanguagePref.TE
    )
    transcript_en: Mapped[str] = mapped_column(Text, default="")
    transcript_te: Mapped[str] = mapped_column(Text, default="")
    recorded_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default_factory=_utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    farmer: Mapped["FarmerProfile"] = relationship(
        back_populates="voice_intros", init=False
    )


# -------------------------------------------------------------------- orders


class OrderRequest(TimestampMixin, Base):
    """A buyer request against one listing, with delivery details."""

    __tablename__ = "order_request"
    __table_args__ = (
        UniqueConstraint("order_code", name="uq_order_code"),
        CheckConstraint("quantity > 0", name="ck_order_qty_positive"),
        CheckConstraint("total_amount >= 0", name="ck_order_total_nonneg"),
        Index("ix_order_status_created", "status", "created_at"),
        Index("ix_order_buyer_status", "buyer_id", "status"),
        Index("ix_order_farmer_status", "farmer_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_code: Mapped[str] = mapped_column(String(24), index=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("crop_listing.id", ondelete="RESTRICT"), index=True
    )
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="RESTRICT"), index=True
    )
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmer_profile.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[QuantityUnit] = mapped_column(
        Enum(QuantityUnit, name="quantity_unit"), default=QuantityUnit.KG
    )
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    delivery_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    fulfilment_mode: Mapped[FulfilmentMode] = mapped_column(
        Enum(FulfilmentMode, name="fulfilment_mode"),
        default=FulfilmentMode.FARM_PICKUP,
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), default=OrderStatus.REQUESTED
    )
    buyer_note: Mapped[str] = mapped_column(Text, default="")
    farmer_note: Mapped[str] = mapped_column(Text, default="")
    distance_km: Mapped[float | None] = mapped_column(Float, default=None)
    requested_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default_factory=_utcnow
    )
    accepted_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    cancelled_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    cancellation_reason: Mapped[str] = mapped_column(String(255), default="")
    completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    listing: Mapped["CropListing"] = relationship(
        back_populates="orders", init=False
    )
    delivery_detail: Mapped["DeliveryDetail | None"] = relationship(
        back_populates="order", uselist=False, init=False
    )
    payments: Mapped[list["PaymentRecord"]] = relationship(
        back_populates="order", init=False
    )
    confirmations: Mapped[list["DeliveryConfirmation"]] = relationship(
        back_populates="order", init=False
    )
    payouts: Mapped[list["FarmerPayout"]] = relationship(
        back_populates="order", init=False
    )
    disputes: Mapped[list["Dispute"]] = relationship(
        back_populates="order", init=False
    )
    conversation: Mapped["Conversation | None"] = relationship(
        back_populates="order", uselist=False, init=False
    )


class DeliveryDetail(TimestampMixin, Base):
    """Where and when the harvest should reach the buyer."""

    __tablename__ = "delivery_detail"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_delivery_detail_order"),
        Index("ix_delivery_slot", "scheduled_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order_request.id", ondelete="CASCADE"), index=True
    )
    contact_name: Mapped[str] = mapped_column(String(120), default="")
    contact_phone: Mapped[str] = mapped_column(String(20), default="")
    address_line: Mapped[str] = mapped_column(String(255), default="")
    village: Mapped[str] = mapped_column(String(120), default="")
    mandal: Mapped[str] = mapped_column(String(120), default="")
    district: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(80), default="Telangana")
    pincode: Mapped[str] = mapped_column(String(10), default="")
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    landmark: Mapped[str] = mapped_column(String(255), default="")
    scheduled_date: Mapped[dt.date | None] = mapped_column(Date, default=None)
    slot_label_en: Mapped[str] = mapped_column(String(80), default="")
    slot_label_te: Mapped[str] = mapped_column(String(80), default="")
    instructions_en: Mapped[str] = mapped_column(Text, default="")
    instructions_te: Mapped[str] = mapped_column(Text, default="")
    dispatched_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    order: Mapped["OrderRequest"] = relationship(
        back_populates="delivery_detail", init=False
    )


class PaymentRecord(TimestampMixin, Base):
    """Razorpay/UPI checkout record. The platform holds funds; not escrow."""

    __tablename__ = "payment_record"
    __table_args__ = (
        UniqueConstraint("razorpay_order_id", name="uq_payment_rzp_order"),
        UniqueConstraint("razorpay_payment_id", name="uq_payment_rzp_payment"),
        CheckConstraint("amount >= 0", name="ck_payment_amount_nonneg"),
        Index("ix_payment_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order_request.id", ondelete="CASCADE"), index=True
    )
    payer_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(64), default=None
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(64), default=None
    )
    razorpay_signature: Mapped[str] = mapped_column(String(255), default="")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"), default=PaymentMethod.UPI
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.CREATED,
    )
    is_platform_held: Mapped[bool] = mapped_column(Boolean, default=True)
    captured_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    refunded_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    refunded_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    failure_reason: Mapped[str] = mapped_column(String(255), default="")
    receipt_note: Mapped[str] = mapped_column(String(255), default="")

    order: Mapped["OrderRequest"] = relationship(
        back_populates="payments", init=False
    )


class DeliveryConfirmation(TimestampMixin, Base):
    """Buyer or farmer confirming the harvest changed hands."""

    __tablename__ = "delivery_confirmation"
    __table_args__ = (
        UniqueConstraint(
            "order_id", "confirmed_by_role", name="uq_confirm_once"
        ),
        Index("ix_confirmation_order", "order_id", "confirmed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order_request.id", ondelete="CASCADE"), index=True
    )
    confirmed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    confirmed_by_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.CUSTOMER
    )
    confirmed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default_factory=_utcnow
    )
    delivered_quantity: Mapped[float | None] = mapped_column(
        Float, default=None
    )
    quality_rating: Mapped[int | None] = mapped_column(Integer, default=None)
    remarks_en: Mapped[str] = mapped_column(Text, default="")
    remarks_te: Mapped[str] = mapped_column(Text, default="")
    proof_file_name: Mapped[str] = mapped_column(String(255), default="")

    order: Mapped["OrderRequest"] = relationship(
        back_populates="confirmations", init=False
    )


class FarmerPayout(TimestampMixin, Base):
    """Manually recorded payout to a farmer after delivery confirmation."""

    __tablename__ = "farmer_payout"
    __table_args__ = (
        CheckConstraint("gross_amount >= 0", name="ck_payout_gross_nonneg"),
        CheckConstraint("net_amount >= 0", name="ck_payout_net_nonneg"),
        Index("ix_payout_status_created", "status", "created_at"),
        Index("ix_payout_farmer_status", "farmer_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order_request.id", ondelete="CASCADE"), index=True
    )
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmer_profile.id", ondelete="RESTRICT"), index=True
    )
    gross_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    platform_fee: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[PayoutStatus] = mapped_column(
        Enum(PayoutStatus, name="payout_status"), default=PayoutStatus.DUE
    )
    method_note: Mapped[str] = mapped_column(
        String(120), default="manual_upi_transfer"
    )
    payout_reference: Mapped[str] = mapped_column(String(120), default="")
    scheduled_for: Mapped[dt.date | None] = mapped_column(Date, default=None)
    paid_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    recorded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    admin_note: Mapped[str] = mapped_column(Text, default="")

    order: Mapped["OrderRequest"] = relationship(
        back_populates="payouts", init=False
    )


class Dispute(TimestampMixin, Base):
    """Buyer or farmer raising a problem with an order."""

    __tablename__ = "dispute"
    __table_args__ = (
        Index("ix_dispute_status_created", "status", "created_at"),
        Index("ix_dispute_order", "order_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("order_request.id", ondelete="CASCADE"), index=True
    )
    raised_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    raised_by_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.CUSTOMER
    )
    category: Mapped[str] = mapped_column(String(60), default="quality")
    subject_en: Mapped[str] = mapped_column(String(160), default="")
    subject_te: Mapped[str] = mapped_column(String(160), default="")
    details_en: Mapped[str] = mapped_column(Text, default="")
    details_te: Mapped[str] = mapped_column(Text, default="")
    evidence_file_name: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status"), default=DisputeStatus.OPEN
    )
    resolution_note: Mapped[str] = mapped_column(Text, default="")
    refund_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    resolved_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    order: Mapped["OrderRequest"] = relationship(
        back_populates="disputes", init=False
    )


# ------------------------------------------------------------- conversations


class Conversation(TimestampMixin, Base):
    """Order-linked bilingual thread between buyer and farmer."""

    __tablename__ = "conversation"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_conversation_order"),
        Index("ix_conversation_last_message", "last_message_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("order_request.id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("crop_listing.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(160), default="")
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    last_message_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    order: Mapped["OrderRequest | None"] = relationship(
        back_populates="conversation", init=False
    )
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        back_populates="conversation", init=False
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", init=False
    )


class ConversationParticipant(TimestampMixin, Base):
    __tablename__ = "conversation_participant"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id", "user_id", name="uq_participant_once"
        ),
        Index("ix_participant_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE")
    )
    role_in_thread: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.CUSTOMER
    )
    last_read_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)

    conversation: Mapped["Conversation"] = relationship(
        back_populates="participants", init=False
    )


class Message(TimestampMixin, Base):
    """Timestamped text or voice-note message in a conversation."""

    __tablename__ = "message"
    __table_args__ = (
        Index("ix_message_conversation_sent", "conversation_id", "sent_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    kind: Mapped[MessageKind] = mapped_column(
        Enum(MessageKind, name="message_kind"), default=MessageKind.TEXT
    )
    body: Mapped[str] = mapped_column(Text, default="")
    body_language: Mapped[LanguagePref] = mapped_column(
        Enum(LanguagePref, name="language_pref"), default=LanguagePref.EN
    )
    voice_file_name: Mapped[str] = mapped_column(String(255), default="")
    voice_duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    sent_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default_factory=_utcnow
    )
    read_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages", init=False
    )


# ------------------------------------------------- market content and audit


class MandiPrice(TimestampMixin, Base):
    """Telangana mandi reference price used for fair-price comparison."""

    __tablename__ = "mandi_price"
    __table_args__ = (
        UniqueConstraint(
            "crop_slug", "mandi_name", "price_date", name="uq_mandi_crop_day"
        ),
        CheckConstraint("modal_price >= 0", name="ck_mandi_modal_nonneg"),
        Index("ix_mandi_crop_date", "crop_slug", "price_date"),
        Index("ix_mandi_district", "district"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    crop_name_en: Mapped[str] = mapped_column(String(120))
    crop_name_te: Mapped[str] = mapped_column(String(120), default="")
    crop_slug: Mapped[str] = mapped_column(String(120), default="")
    variety: Mapped[str] = mapped_column(String(120), default="")
    mandi_name: Mapped[str] = mapped_column(String(120), default="")
    mandal: Mapped[str] = mapped_column(String(120), default="")
    district: Mapped[str] = mapped_column(String(120), default="")
    state: Mapped[str] = mapped_column(String(80), default="Telangana")
    unit: Mapped[QuantityUnit] = mapped_column(
        Enum(QuantityUnit, name="quantity_unit"), default=QuantityUnit.QUINTAL
    )
    min_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    max_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    modal_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    price_date: Mapped[dt.date | None] = mapped_column(Date, default=None)
    source_name: Mapped[str] = mapped_column(String(160), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AdvisoryEntry(TimestampMixin, Base):
    """Sourced ICAR/KVK crop guidance shown in the advisory library."""

    __tablename__ = "advisory_entry"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_advisory_slug"),
        Index("ix_advisory_crop_season", "crop_slug", "season"),
        Index("ix_advisory_published", "is_published", "reviewed_on"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    slug: Mapped[str] = mapped_column(String(160), index=True)
    title_en: Mapped[str] = mapped_column(String(200))
    title_te: Mapped[str] = mapped_column(String(200), default="")
    summary_en: Mapped[str] = mapped_column(Text, default="")
    summary_te: Mapped[str] = mapped_column(Text, default="")
    body_en: Mapped[str] = mapped_column(Text, default="")
    body_te: Mapped[str] = mapped_column(Text, default="")
    crop_name_en: Mapped[str] = mapped_column(String(120), default="")
    crop_name_te: Mapped[str] = mapped_column(String(120), default="")
    crop_slug: Mapped[str] = mapped_column(String(120), default="")
    topic: Mapped[str] = mapped_column(String(80), default="general")
    season: Mapped[AdvisorySeason] = mapped_column(
        Enum(AdvisorySeason, name="advisory_season"),
        default=AdvisorySeason.ALL_YEAR,
    )
    source_type: Mapped[AdvisorySource] = mapped_column(
        Enum(AdvisorySource, name="advisory_source"),
        default=AdvisorySource.ICAR,
    )
    source_name: Mapped[str] = mapped_column(String(200), default="")
    source_url: Mapped[str] = mapped_column(String(500), default="")
    reviewed_on: Mapped[dt.date | None] = mapped_column(Date, default=None)
    reviewed_by: Mapped[str] = mapped_column(String(160), default="")
    disclaimer_en: Mapped[str] = mapped_column(Text, default="")
    disclaimer_te: Mapped[str] = mapped_column(Text, default="")
    hero_image_name: Mapped[str] = mapped_column(String(255), default="")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )


class AdminAuditLog(TimestampMixin, Base):
    """Every operator action in the control room, for accountability."""

    __tablename__ = "admin_audit_log"
    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_actor_created", "actor_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"), default=None
    )
    actor_email: Mapped[str] = mapped_column(String(255), default="")
    action: Mapped[str] = mapped_column(String(80), default="")
    entity_type: Mapped[str] = mapped_column(String(60), default="")
    entity_id: Mapped[int | None] = mapped_column(Integer, default=None)
    before_state: Mapped[str] = mapped_column(Text, default="")
    after_state: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")
    ip_address: Mapped[str] = mapped_column(String(64), default="")
