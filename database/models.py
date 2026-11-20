"""
SQLAlchemy 2.0 ORM Models
Defines all 35 entities conforming strictly to 04_DATABASE_SCHEMA.md.
Includes complete relationships, foreign keys, timestamps, and credentials.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, BigInteger, Boolean, DateTime, Date, Time,
    Text, ForeignKey, PrimaryKeyConstraint, UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
from database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

# Primary Key BigSerial type that works in both PostgreSQL (BIGINT/BIGSERIAL) and SQLite (INTEGER ROWID)
PK_BIGINT = BigInteger().with_variant(Integer, "sqlite")

# ==================== 1. USERS & IDENTITY ====================

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    role = Column(String(20), nullable=False, index=True) # buyer, farmer, driver, hub_staff, admin, super_admin
    name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=True)
    password_hash = Column(String(255), nullable=False) # Bcrypt hash of user credential
    language = Column(String(5), default="kn")
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    farmer_profile = relationship("Farmer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    buyer_profile = relationship("Buyer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    driver_profile = relationship("Driver", back_populates="user", uselist=False, cascade="all, delete-orphan")
    staff_hubs = relationship("HubStaff", back_populates="user", cascade="all, delete-orphan")

# ==================== 2. HUBS & VEHICLES ====================

class Hub(Base):
    __tablename__ = "hubs"

    id = Column(String(64), primary_key=True)
    name = Column(String(120), nullable=False)
    type = Column(String(20), nullable=False) # 'main', 'village', 'city'
    parent_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=True)
    capacity_kg = Column(Float, nullable=True)
    has_cold_room = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    staff = relationship("HubStaff", back_populates="hub")
    stock_statuses = relationship("HubStockStatus", back_populates="hub")

class HubStaff(Base):
    __tablename__ = "hub_staff"

    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="staff_hubs")
    hub = relationship("Hub", back_populates="staff")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(64), primary_key=True)
    reg_no = Column(String(20), unique=True, nullable=False)
    type = Column(String(60), nullable=False)
    capacity_kg = Column(Float, nullable=False)
    ownership = Column(String(10), default="rent") # 'own' or 'rent'
    active = Column(Boolean, default=True)

    drivers = relationship("Driver", back_populates="vehicle")
    trips = relationship("Trip", back_populates="vehicle")

# ==================== 3. ACTOR PROFILES ====================

class Farmer(Base):
    __tablename__ = "farmers"

    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    village = Column(String(120), nullable=True)
    taluk = Column(String(120), nullable=True)
    district = Column(String(120), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    nearest_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    land_acres = Column(Float, nullable=True)
    default_min_kg = Column(Float, default=20.0)
    upi_id = Column(String(80), nullable=True)
    bank_account_ref = Column(String(80), nullable=True)
    reliability_score = Column(Float, default=5.0)
    approved = Column(Boolean, default=True)

    user = relationship("User", back_populates="farmer_profile")
    nearest_hub = relationship("Hub")
    crop_thresholds = relationship("FarmerCropThreshold", back_populates="farmer", cascade="all, delete-orphan")
    listings = relationship("FarmerListing", back_populates="farmer")

class Buyer(Base):
    __tablename__ = "buyers"

    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    business_name = Column(String(160), nullable=False)
    business_type = Column(String(40), nullable=True)
    gstin = Column(String(15), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    delivery_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    credit_limit = Column(BigInteger, default=0) # in paise
    credit_days = Column(Integer, default=0)
    credit_due = Column(BigInteger, default=0) # in paise
    approved = Column(Boolean, default=True)

    user = relationship("User", back_populates="buyer_profile")
    delivery_hub = relationship("Hub")
    orders = relationship("Order", back_populates="buyer")

class Driver(Base):
    __tablename__ = "drivers"

    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    licence_no = Column(String(30), nullable=True)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    home_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    on_duty = Column(Boolean, default=False)

    user = relationship("User", back_populates="driver_profile")
    vehicle = relationship("Vehicle", back_populates="drivers")
    home_hub = relationship("Hub")
    trips = relationship("Trip", back_populates="driver")

# ==================== 4. CROPS & THRESHOLDS ====================

class Crop(Base):
    __tablename__ = "crops"

    id = Column(String(64), primary_key=True)
    slug = Column(String(60), unique=True, nullable=False)
    name_en = Column(String(80), nullable=False)
    name_kn = Column(String(80), nullable=True)
    category = Column(String(40), nullable=False)
    is_organic = Column(Boolean, default=False)
    unit = Column(String(10), default="kg")
    shelf_life_hours = Column(Integer, nullable=True)
    shelf_life_days = Column(Integer, nullable=True)
    perishability = Column(Integer, default=3)
    min_order_kg = Column(Float, default=10.0)
    default_min_kg = Column(Float, default=20.0)
    icon_url = Column(Text, nullable=True)
    image_emoji = Column(String(10), nullable=True)
    active = Column(Boolean, default=True)

class FarmerCropThreshold(Base):
    __tablename__ = "farmer_crop_thresholds"

    farmer_id = Column(String(64), ForeignKey("farmers.user_id", ondelete="CASCADE"), primary_key=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)
    min_kg = Column(Float, nullable=False)

    farmer = relationship("Farmer", back_populates="crop_thresholds")
    crop = relationship("Crop")

# ==================== 5. STOCK MATRIX & LEDGER ====================

class HubStockStatus(Base):
    __tablename__ = "hub_stock_status"

    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), primary_key=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)
    status = Column(String(20), nullable=False, default="OUT") # 'OUT', 'LOW', 'SUFFICIENT'
    suggested = Column(String(20), nullable=True)
    set_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    set_at = Column(DateTime(timezone=True), default=utc_now)

    hub = relationship("Hub", back_populates="stock_statuses")
    crop = relationship("Crop")

class HubStockStatusHistory(Base):
    __tablename__ = "hub_stock_status_history"

    id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=True)
    source = Column(String(10), default="manual")
    set_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    at = Column(DateTime(timezone=True), default=utc_now)

class StockLedger(Base):
    __tablename__ = "stock_ledger"

    id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    delta_kg = Column(Float, nullable=False)
    reason = Column(String(30), nullable=False) # 'PICKUP', 'TRANSFER_IN', 'TRANSFER_OUT', 'SALE', 'WASTAGE', 'ADJUSTMENT'
    ref_type = Column(String(30), nullable=True)
    ref_id = Column(String(64), nullable=True)
    grade = Column(String(10), nullable=True)
    created_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

# ==================== 6. SUPPLY: LISTINGS ====================

class FarmerListing(Base):
    __tablename__ = "farmer_listings"

    id = Column(String(64), primary_key=True)
    farmer_id = Column(String(64), ForeignKey("farmers.user_id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    listing_date = Column(Date, nullable=False)
    est_kg = Column(Float, nullable=False)
    ready_from = Column(DateTime(timezone=True), nullable=True)
    ready_by = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="DRAFT") # 'DRAFT', 'INELIGIBLE', 'ELIGIBLE', 'SCHEDULED', 'COLLECTED'
    min_kg_applied = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (UniqueConstraint("farmer_id", "crop_id", "listing_date", name="uq_farmer_listing_date"),)

    farmer = relationship("Farmer", back_populates="listings")
    crop = relationship("Crop")

# ==================== 7. DEMAND: ORDERS ====================

class Order(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True)
    buyer_id = Column(String(64), ForeignKey("buyers.user_id", ondelete="CASCADE"), nullable=False)
    delivery_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    delivery_date = Column(Date, nullable=False)
    slot_start = Column(Time, nullable=True)
    slot_end = Column(Time, nullable=True)
    slot = Column(String(30), nullable=True)
    status = Column(String(30), default="PLACED") # 'PLACED', 'CONFIRMED', 'ASSIGNED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'
    subtotal = Column(BigInteger, default=0) # paise
    delivery_fee = Column(BigInteger, default=0) # paise
    total = Column(BigInteger, default=0) # paise
    payment_mode = Column(String(10), default="PREPAID")
    payment_status = Column(String(20), default="PENDING")
    delivery_otp = Column(String(6), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    buyer = relationship("Buyer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), nullable=False)
    qty_kg = Column(Float, nullable=False)
    confirmed_kg = Column(Float, nullable=True)
    delivered_kg = Column(Float, nullable=True)
    rejected_kg = Column(Float, default=0.0)
    price_per_kg_locked = Column(BigInteger, nullable=False) # paise
    reject_reason = Column(Text, nullable=True)
    note = Column(String(20), default="FULL")

    order = relationship("Order", back_populates="items")
    crop = relationship("Crop")

# ==================== 8. LOGISTICS: TRIPS, STOPS, PINGS ====================

class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(64), primary_key=True)
    type = Column(String(20), nullable=False) # 'FIRST_MILE', 'MIDDLE_MILE', 'LAST_MILE', 'TRANSFER'
    status = Column(String(20), default="ASSIGNED") # 'ASSIGNED', 'STARTED', 'AT_HUB', 'RETURNED', 'CLOSED'
    driver_id = Column(String(64), ForeignKey("drivers.user_id", ondelete="RESTRICT"), nullable=False)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    origin_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    dest_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    assigned_by = Column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    date = Column(Date, nullable=False)
    planned_start = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    planned_km = Column(Float, nullable=True)
    planned_minutes = Column(Integer, nullable=True)
    total_planned_kg = Column(Float, default=0.0)
    total_actual_kg = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    driver = relationship("Driver", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    stops = relationship("TripStop", back_populates="trip", cascade="all, delete-orphan", order_by="TripStop.seq")

class TripStop(Base):
    __tablename__ = "trip_stops"

    id = Column(String(64), primary_key=True)
    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    seq = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False) # 'PICKUP', 'HUB', 'DELIVERY'
    status = Column(String(20), default="PLANNED") # 'PLANNED', 'EN_ROUTE', 'ARRIVED', 'COMPLETED', 'SKIPPED'
    farmer_id = Column(String(64), ForeignKey("farmers.user_id", ondelete="SET NULL"), nullable=True)
    buyer_order_id = Column(String(64), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(160), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    expected_kg = Column(Float, nullable=True)
    actual_kg = Column(Float, nullable=True)
    eta = Column(String(30), nullable=True)
    distance_km = Column(Float, nullable=True)
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    skip_reason = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("trip_id", "seq", name="uq_trip_stop_seq"),)

    trip = relationship("Trip", back_populates="stops")
    receipts = relationship("PickupReceipt", back_populates="stop", cascade="all, delete-orphan")

class PickupReceipt(Base):
    __tablename__ = "pickup_receipts"

    id = Column(String(64), primary_key=True)
    trip_stop_id = Column(String(64), ForeignKey("trip_stops.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(String(64), ForeignKey("farmer_listings.id", ondelete="SET NULL"), nullable=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False)
    kg_received = Column(Float, nullable=False)
    grade = Column(String(10), default="A")
    photo_url = Column(Text, nullable=True)
    farmer_confirmed = Column(Boolean, default=False)
    client_event_id = Column(String(64), unique=True, nullable=True)
    recorded_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=utc_now)

    stop = relationship("TripStop", back_populates="receipts")
    crop = relationship("Crop")

class HubReceipt(Base):
    __tablename__ = "hub_receipts"

    id = Column(String(64), primary_key=True)
    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)
    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False)
    kg_driver = Column(Float, nullable=True)
    kg_hub = Column(Float, nullable=True)
    variance_pct = Column(Float, nullable=True)
    grade_a_kg = Column(Float, nullable=True)
    grade_b_kg = Column(Float, nullable=True)
    reject_kg = Column(Float, nullable=True)
    recorded_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=utc_now)

class LocationPing(Base):
    __tablename__ = "location_pings"

    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True)
    ts = Column(DateTime(timezone=True), primary_key=True)
    driver_id = Column(String(64), ForeignKey("drivers.user_id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    accuracy_m = Column(Float, nullable=True)

class TransferRequest(Base):
    __tablename__ = "transfer_requests"

    id = Column(String(64), primary_key=True)
    from_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False)
    to_hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), nullable=False)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False)
    requested_kg = Column(Float, nullable=False)
    sent_kg = Column(Float, nullable=True)
    received_kg = Column(Float, nullable=True)
    status = Column(String(20), default="SUGGESTED") # 'SUGGESTED', 'REQUESTED', 'APPROVED', 'IN_TRANSIT', 'RECEIVED'
    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    requested_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

# ==================== 9. PRICING & FORECASTS ====================

class MarketPrice(Base):
    __tablename__ = "market_prices"

    date = Column(Date, primary_key=True)
    market = Column(String(80), primary_key=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    modal_price = Column(Float, nullable=True)
    arrivals_qtl = Column(Float, nullable=True)
    source = Column(String(30), default="agmarknet")

class WeatherDaily(Base):
    __tablename__ = "weather_daily"

    date = Column(Date, primary_key=True)
    location_key = Column(String(60), primary_key=True)
    is_forecast = Column(Boolean, primary_key=True, default=False)
    rain_mm = Column(Float, nullable=True)
    tmax = Column(Float, nullable=True)
    tmin = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)

class PriceForecast(Base):
    __tablename__ = "price_forecasts"

    date = Column(Date, primary_key=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)
    market = Column(String(80), primary_key=True)
    model_version = Column(String(30), primary_key=True)
    p10 = Column(Float, nullable=False)
    p50 = Column(Float, nullable=False)
    p90 = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    date = Column(Date, primary_key=True)
    hub_id = Column(String(64), ForeignKey("hubs.id", ondelete="CASCADE"), primary_key=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)
    model_version = Column(String(30), primary_key=True)
    q10 = Column(Float, nullable=False)
    q50 = Column(Float, nullable=False)
    q90 = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class PublishedPrice(Base):
    __tablename__ = "published_prices"

    date = Column(Date, primary_key=True)
    crop_id = Column(String(64), ForeignKey("crops.id", ondelete="CASCADE"), primary_key=True)
    low = Column(Float, nullable=False) # paise per kg
    high = Column(Float, nullable=False) # paise per kg
    reference = Column(Float, nullable=False) # paise per kg
    overridden = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    published_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at = Column(DateTime(timezone=True), default=utc_now)

# ==================== 10. PAYMENTS & SETTLEMENTS ====================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(64), primary_key=True)
    party_id = Column(String(64), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    direction = Column(String(10), nullable=False) # 'IN', 'OUT'
    amount = Column(BigInteger, nullable=False) # paise
    status = Column(String(20), default="PENDING")
    gateway_ref = Column(String(80), nullable=True)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    settlement_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(String(64), primary_key=True)
    farmer_id = Column(String(64), ForeignKey("farmers.user_id", ondelete="RESTRICT"), nullable=False)
    settle_date = Column(Date, nullable=False)
    accepted_kg = Column(Float, nullable=False)
    gross = Column(BigInteger, nullable=False) # paise
    commission = Column(BigInteger, nullable=False) # paise
    logistics_share = Column(BigInteger, nullable=False) # paise
    net = Column(BigInteger, nullable=False) # paise
    status = Column(String(15), default="DRAFT") # 'DRAFT', 'APPROVED', 'PAID'
    approved_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("farmer_id", "settle_date", name="uq_farmer_settlement_date"),)

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    txn_id = Column(String(64), nullable=False)
    account = Column(String(40), nullable=False)
    party_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    debit = Column(BigInteger, default=0)
    credit = Column(BigInteger, default=0)
    ref_type = Column(String(30), nullable=True)
    ref_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

# ==================== 11. PLATFORM & SETTINGS ====================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(10), nullable=False) # 'push', 'sms', 'whatsapp'
    template = Column(String(60), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(10), default="SENT")
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Event(Base):
    __tablename__ = "events"

    id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    type = Column(String(60), nullable=False)
    entity_id = Column(String(64), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(PK_BIGINT, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(60), nullable=False)
    entity = Column(String(40), nullable=False)
    entity_id = Column(String(64), nullable=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(60), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(64), primary_key=True)
    trip_id = Column(String(64), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    type = Column(String(30), nullable=False) # 'BREAKDOWN', 'ACCIDENT', 'DELAY'
    notes = Column(Text, nullable=True)
    reported_by = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
