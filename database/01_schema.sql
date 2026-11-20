-- ==============================================================================
-- KRISHILINK PLATFORM - PRODUCTION DATABASE SCHEMA
-- PostgreSQL 16+ with PostGIS and pgcrypto extensions
-- Conforms strictly to 03_ARCHITECTURE.md, 04_DATABASE_SCHEMA.md, 05_API_SPEC.md
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. ENUMS
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('buyer', 'farmer', 'driver', 'hub_staff', 'admin', 'super_admin');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE hub_type AS ENUM ('main', 'village', 'city');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE stock_status AS ENUM ('OUT', 'LOW', 'SUFFICIENT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE listing_status AS ENUM ('DRAFT', 'INELIGIBLE', 'ELIGIBLE', 'SCHEDULED', 'COLLECTED', 'CANCELLED', 'EXPIRED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE order_status AS ENUM ('PLACED', 'CONFIRMED', 'PARTIAL', 'ASSIGNED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE trip_type AS ENUM ('FIRST_MILE', 'MIDDLE_MILE', 'LAST_MILE', 'TRANSFER');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE trip_status AS ENUM ('ASSIGNED', 'ACKNOWLEDGED', 'STARTED', 'AT_HUB', 'RETURNED', 'CLOSED', 'CANCELLED', 'INCIDENT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE stop_type AS ENUM ('PICKUP', 'HUB', 'DELIVERY');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE stop_status AS ENUM ('PLANNED', 'EN_ROUTE', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED', 'SKIPPED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE transfer_status AS ENUM ('SUGGESTED', 'REQUESTED', 'APPROVED', 'ASSIGNED', 'IN_TRANSIT', 'RECEIVED', 'REJECTED', 'CANCELLED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE grade AS ENUM ('A', 'B', 'REJECT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE ledger_reason AS ENUM ('PICKUP', 'TRANSFER_IN', 'TRANSFER_OUT', 'SALE', 'WASTAGE', 'ADJUSTMENT', 'RETURN');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE payment_direction AS ENUM ('IN', 'OUT');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- ==============================================================================
-- 3. IDENTITY, CREDENTIALS & HUBS
-- ==============================================================================

-- 3.1 Users table (All Farmers, Buyers, Drivers, Admins, Hub Staff)
CREATE TABLE IF NOT EXISTS users (
    id            VARCHAR(64) PRIMARY KEY,
    phone         VARCHAR(20) UNIQUE NOT NULL,
    role          user_role NOT NULL,
    name          VARCHAR(120) NOT NULL,
    email         VARCHAR(120),
    password_hash VARCHAR(255) NOT NULL, -- Bcrypt hash of user credentials
    language      VARCHAR(5) DEFAULT 'kn', -- 'kn' (Kannada), 'en' (English)
    is_active     BOOLEAN DEFAULT true,
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 3.2 Hubs table (Village Mini Hubs, Central Yeshwanthpur Hub, City Mini Hubs)
CREATE TABLE IF NOT EXISTS hubs (
    id            VARCHAR(64) PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    type          hub_type NOT NULL,
    parent_hub_id VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    location      geography(Point, 4326) NOT NULL,
    latitude      NUMERIC(10, 6) NOT NULL,
    longitude     NUMERIC(10, 6) NOT NULL,
    address       TEXT,
    capacity_kg   NUMERIC(10, 2),
    has_cold_room BOOLEAN DEFAULT false,
    active        BOOLEAN DEFAULT true,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 3.3 Hub Staff Mapping (Links staff users to specific hubs)
CREATE TABLE IF NOT EXISTS hub_staff (
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
    hub_id  VARCHAR(64) REFERENCES hubs(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, hub_id)
);

-- 3.4 Farmers Profile
CREATE TABLE IF NOT EXISTS farmers (
    user_id           VARCHAR(64) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    village           VARCHAR(120),
    taluk             VARCHAR(120),
    district          VARCHAR(120),
    location          geography(Point, 4326) NOT NULL,
    latitude          NUMERIC(10, 6) NOT NULL,
    longitude         NUMERIC(10, 6) NOT NULL,
    nearest_hub_id    VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    land_acres        NUMERIC(6, 2),
    default_min_kg    NUMERIC(8, 2) DEFAULT 20.00,
    upi_id            VARCHAR(80),
    bank_account_ref  VARCHAR(80),
    reliability_score NUMERIC(4, 2) DEFAULT 5.00,
    approved          BOOLEAN DEFAULT false
);

-- 3.5 Buyers Profile (Restaurants, Caterers, Hostels, Wholesalers)
CREATE TABLE IF NOT EXISTS buyers (
    user_id         VARCHAR(64) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    business_name   VARCHAR(160) NOT NULL,
    business_type   VARCHAR(40),
    gstin           VARCHAR(15),
    address         TEXT,
    location        geography(Point, 4326) NOT NULL,
    latitude        NUMERIC(10, 6) NOT NULL,
    longitude       NUMERIC(10, 6) NOT NULL,
    delivery_hub_id VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    credit_limit    BIGINT DEFAULT 0, -- paise (e.g. 15000000 = ₹1,50,000)
    credit_days     INT DEFAULT 0,
    credit_due      BIGINT DEFAULT 0, -- paise
    approved        BOOLEAN DEFAULT false
);

-- 3.6 Vehicles
CREATE TABLE IF NOT EXISTS vehicles (
    id          VARCHAR(64) PRIMARY KEY,
    reg_no      VARCHAR(20) UNIQUE NOT NULL,
    type        VARCHAR(60) NOT NULL, -- e.g. 'Tata Ace (Chota Hathi)', 'Mahindra Bolero Maxi Truck'
    capacity_kg NUMERIC(8, 2) NOT NULL,
    ownership   VARCHAR(10) CHECK (ownership IN ('own', 'rent')),
    active      BOOLEAN DEFAULT true
);

-- 3.7 Drivers Profile
CREATE TABLE IF NOT EXISTS drivers (
    user_id     VARCHAR(64) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    licence_no  VARCHAR(30),
    vehicle_id  VARCHAR(64) REFERENCES vehicles(id) ON DELETE SET NULL,
    home_hub_id VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    on_duty     BOOLEAN DEFAULT false
);

-- ==============================================================================
-- 4. CROPS & THRESHOLDS
-- ==============================================================================

-- 4.1 Crops Catalog
CREATE TABLE IF NOT EXISTS crops (
    id               VARCHAR(64) PRIMARY KEY,
    slug             VARCHAR(60) UNIQUE NOT NULL,
    name_en          VARCHAR(80) NOT NULL,
    name_kn          VARCHAR(80),
    category         VARCHAR(40), -- 'fruit_veg', 'roots', 'leafy', 'herbs'
    is_organic       BOOLEAN DEFAULT false,
    unit             VARCHAR(10) DEFAULT 'kg',
    shelf_life_hours INT,
    shelf_life_days  INT,
    perishability    SMALLINT DEFAULT 3, -- 1 (hardy) to 5 (very perishable)
    min_order_kg     NUMERIC(8, 2) DEFAULT 10.00,
    default_min_kg   NUMERIC(8, 2) DEFAULT 20.00,
    icon_url         TEXT,
    image_emoji      VARCHAR(10),
    active           BOOLEAN DEFAULT true
);

-- 4.2 Farmer Crop Thresholds (Overrides default_min_kg for specific crops)
CREATE TABLE IF NOT EXISTS farmer_crop_thresholds (
    farmer_id VARCHAR(64) REFERENCES farmers(user_id) ON DELETE CASCADE,
    crop_id   VARCHAR(64) REFERENCES crops(id) ON DELETE CASCADE,
    min_kg    NUMERIC(8, 2) NOT NULL,
    PRIMARY KEY (farmer_id, crop_id)
);

-- ==============================================================================
-- 5. STOCK MANAGEMENT (THREE-BUTTON MATRIX & LEDGER)
-- ==============================================================================

-- 5.1 Human-Facing Hub Stock Status (OUT / LOW / SUFFICIENT)
CREATE TABLE IF NOT EXISTS hub_stock_status (
    hub_id    VARCHAR(64) REFERENCES hubs(id) ON DELETE CASCADE,
    crop_id   VARCHAR(64) REFERENCES crops(id) ON DELETE CASCADE,
    status    stock_status NOT NULL DEFAULT 'OUT',
    suggested stock_status, -- ML / system suggestion
    set_by    VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    set_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (hub_id, crop_id)
);

-- 5.2 Stock Status Audit History
CREATE TABLE IF NOT EXISTS hub_stock_status_history (
    id         BIGSERIAL PRIMARY KEY,
    hub_id     VARCHAR(64) REFERENCES hubs(id) ON DELETE CASCADE,
    crop_id    VARCHAR(64) REFERENCES crops(id) ON DELETE CASCADE,
    old_status stock_status,
    new_status stock_status,
    source     VARCHAR(10) DEFAULT 'manual', -- 'manual' | 'system'
    set_by     VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    at         TIMESTAMPTZ DEFAULT NOW()
);

-- 5.3 Stock Ledger (Audit trail of every kg entering or leaving hubs)
CREATE TABLE IF NOT EXISTS stock_ledger (
    id         BIGSERIAL PRIMARY KEY,
    hub_id     VARCHAR(64) NOT NULL REFERENCES hubs(id) ON DELETE CASCADE,
    crop_id    VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    delta_kg   NUMERIC(12, 3) NOT NULL, -- positive for IN, negative for OUT
    reason     ledger_reason NOT NULL,
    ref_type   VARCHAR(30), -- 'pickup', 'order', 'transfer', 'adjustment'
    ref_id     VARCHAR(64),
    grade      grade,
    created_by VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5.4 Current Stock Quantity View
CREATE OR REPLACE VIEW hub_stock_current AS
SELECT 
    hub_id, 
    crop_id, 
    COALESCE(SUM(delta_kg), 0) AS stock_kg
FROM stock_ledger 
GROUP BY hub_id, crop_id;

-- ==============================================================================
-- 6. SUPPLY (FARMER LISTINGS & PICKUP RECEIPTS)
-- ==============================================================================

-- 6.1 Farmer Listings ("What I have ready today")
CREATE TABLE IF NOT EXISTS farmer_listings (
    id             VARCHAR(64) PRIMARY KEY,
    farmer_id      VARCHAR(64) NOT NULL REFERENCES farmers(user_id) ON DELETE CASCADE,
    crop_id        VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    listing_date   DATE NOT NULL,
    est_kg         NUMERIC(8, 2) NOT NULL,
    ready_from     TIMESTAMPTZ,
    ready_by       TIMESTAMPTZ,
    status         listing_status DEFAULT 'DRAFT',
    min_kg_applied NUMERIC(8, 2),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_farmer_crop_date UNIQUE (farmer_id, crop_id, listing_date)
);

-- ==============================================================================
-- 7. DEMAND (BUYER ORDERS & ORDER ITEMS)
-- ==============================================================================

-- 7.1 Orders
CREATE TABLE IF NOT EXISTS orders (
    id              VARCHAR(64) PRIMARY KEY,
    buyer_id        VARCHAR(64) NOT NULL REFERENCES buyers(user_id) ON DELETE CASCADE,
    delivery_hub_id VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    delivery_date   DATE NOT NULL,
    slot_start      TIME,
    slot_end        TIME,
    slot            VARCHAR(30),
    status          order_status DEFAULT 'PLACED',
    subtotal        BIGINT, -- paise
    delivery_fee    BIGINT, -- paise
    total           BIGINT, -- paise
    payment_mode    VARCHAR(10) CHECK (payment_mode IN ('PREPAID', 'CREDIT', 'UPI')),
    payment_status  payment_status DEFAULT 'PENDING',
    delivery_otp    VARCHAR(6),
    address         TEXT,
    latitude        NUMERIC(10, 6),
    longitude       NUMERIC(10, 6),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 7.2 Order Items
CREATE TABLE IF NOT EXISTS order_items (
    id                  VARCHAR(64) PRIMARY KEY,
    order_id            VARCHAR(64) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    crop_id             VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    qty_kg              NUMERIC(8, 2) NOT NULL,
    confirmed_kg        NUMERIC(8, 2),
    delivered_kg        NUMERIC(8, 2),
    rejected_kg         NUMERIC(8, 2) DEFAULT 0.00,
    price_per_kg_locked BIGINT, -- locked price in paise per kg
    reject_reason       TEXT,
    note                VARCHAR(20) DEFAULT 'FULL' -- 'FULL' or 'PARTIAL'
);

-- ==============================================================================
-- 8. LOGISTICS (TRIPS, STOPS, RECEIPTS, TRACKING, TRANSFERS)
-- ==============================================================================

-- 8.1 Trips (First Mile, Middle Mile, Last Mile, Transfer)
CREATE TABLE IF NOT EXISTS trips (
    id               VARCHAR(64) PRIMARY KEY,
    type             trip_type NOT NULL,
    status           trip_status DEFAULT 'ASSIGNED',
    driver_id        VARCHAR(64) NOT NULL REFERENCES drivers(user_id) ON DELETE RESTRICT,
    vehicle_id       VARCHAR(64) NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    origin_hub_id    VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    dest_hub_id      VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    assigned_by      VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    date             DATE NOT NULL,
    planned_start    TIMESTAMPTZ,
    started_at       TIMESTAMPTZ,
    ended_at         TIMESTAMPTZ,
    planned_route    geography(LineString, 4326),
    planned_km       NUMERIC(8, 2),
    planned_minutes  INT,
    total_planned_kg NUMERIC(8, 2) DEFAULT 0.00,
    total_actual_kg  NUMERIC(8, 2) DEFAULT 0.00,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 8.2 Trip Stops
CREATE TABLE IF NOT EXISTS trip_stops (
    id             VARCHAR(64) PRIMARY KEY,
    trip_id        VARCHAR(64) NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    seq            INT NOT NULL,
    type           stop_type NOT NULL,
    status         stop_status DEFAULT 'PLANNED',
    farmer_id      VARCHAR(64) REFERENCES farmers(user_id) ON DELETE SET NULL,
    buyer_order_id VARCHAR(64) REFERENCES orders(id) ON DELETE SET NULL,
    hub_id         VARCHAR(64) REFERENCES hubs(id) ON DELETE SET NULL,
    name           VARCHAR(160),
    address        TEXT,
    phone          VARCHAR(20),
    location       geography(Point, 4326) NOT NULL,
    latitude       NUMERIC(10, 6) NOT NULL,
    longitude      NUMERIC(10, 6) NOT NULL,
    expected_kg    NUMERIC(8, 2),
    actual_kg      NUMERIC(8, 2),
    eta            VARCHAR(30),
    distance_km    NUMERIC(8, 2),
    arrived_at     TIMESTAMPTZ,
    completed_at   TIMESTAMPTZ,
    skip_reason    TEXT,
    CONSTRAINT uq_trip_seq UNIQUE (trip_id, seq)
);

-- 8.3 Pickup Receipts (Executed at farm during collection)
CREATE TABLE IF NOT EXISTS pickup_receipts (
    id               VARCHAR(64) PRIMARY KEY,
    trip_stop_id     VARCHAR(64) NOT NULL REFERENCES trip_stops(id) ON DELETE CASCADE,
    listing_id       VARCHAR(64) REFERENCES farmer_listings(id) ON DELETE SET NULL,
    crop_id          VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE RESTRICT,
    kg_received      NUMERIC(8, 2) NOT NULL,
    grade            grade DEFAULT 'A',
    photo_url        TEXT,
    farmer_confirmed BOOLEAN DEFAULT false,
    client_event_id  VARCHAR(64) UNIQUE, -- idempotency key for offline sync
    recorded_by      VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    recorded_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 8.4 Hub Receipts (Second weigh-in at hub to detect weight variance)
CREATE TABLE IF NOT EXISTS hub_receipts (
    id           VARCHAR(64) PRIMARY KEY,
    trip_id      VARCHAR(64) REFERENCES trips(id) ON DELETE CASCADE,
    hub_id       VARCHAR(64) REFERENCES hubs(id) ON DELETE CASCADE,
    crop_id      VARCHAR(64) REFERENCES crops(id) ON DELETE RESTRICT,
    kg_driver    NUMERIC(10, 3),
    kg_hub       NUMERIC(10, 3),
    variance_pct NUMERIC(6, 2),
    grade_a_kg   NUMERIC(10, 3),
    grade_b_kg   NUMERIC(10, 3),
    reject_kg    NUMERIC(10, 3),
    recorded_by  VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    recorded_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 8.5 Location Pings (Live GPS Tracking)
CREATE TABLE IF NOT EXISTS location_pings (
    trip_id    VARCHAR(64) NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    driver_id  VARCHAR(64) REFERENCES drivers(user_id) ON DELETE SET NULL,
    ts         TIMESTAMPTZ NOT NULL,
    location   geography(Point, 4326) NOT NULL,
    latitude   NUMERIC(10, 6) NOT NULL,
    longitude  NUMERIC(10, 6) NOT NULL,
    speed_kmh  REAL,
    heading    REAL,
    accuracy_m REAL,
    PRIMARY KEY (trip_id, ts)
);

-- 8.6 Transfer Requests (Lateral Stock Transfers between Hubs)
CREATE TABLE IF NOT EXISTS transfer_requests (
    id           VARCHAR(64) PRIMARY KEY,
    from_hub_id  VARCHAR(64) NOT NULL REFERENCES hubs(id) ON DELETE CASCADE,
    to_hub_id    VARCHAR(64) NOT NULL REFERENCES hubs(id) ON DELETE CASCADE,
    crop_id      VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE RESTRICT,
    requested_kg NUMERIC(10, 2) NOT NULL,
    sent_kg      NUMERIC(10, 2),
    received_kg  NUMERIC(10, 2),
    status       transfer_status DEFAULT 'SUGGESTED',
    trip_id      VARCHAR(64) REFERENCES trips(id) ON DELETE SET NULL,
    requested_by VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    approved_by  VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 9. PRICING & ML FORECASTS
-- ==============================================================================

-- 9.1 Raw Mandi Market Prices (Agmarknet)
CREATE TABLE IF NOT EXISTS market_prices (
    date         DATE NOT NULL,
    market       VARCHAR(80) NOT NULL,
    crop_id      VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    min_price    NUMERIC(8, 2),
    max_price    NUMERIC(8, 2),
    modal_price  NUMERIC(8, 2),
    arrivals_qtl NUMERIC(12, 2),
    source       VARCHAR(30) DEFAULT 'agmarknet',
    PRIMARY KEY (date, market, crop_id)
);

-- 9.2 Daily Weather (Open-Meteo)
CREATE TABLE IF NOT EXISTS weather_daily (
    date         DATE NOT NULL,
    location_key VARCHAR(60) NOT NULL,
    rain_mm      NUMERIC(6, 2),
    tmax         NUMERIC(4, 1),
    tmin         NUMERIC(4, 1),
    humidity     NUMERIC(5, 2),
    is_forecast  BOOLEAN DEFAULT false,
    PRIMARY KEY (date, location_key, is_forecast)
);

-- 9.3 ML Price Forecasts (p10, p50, p90)
CREATE TABLE IF NOT EXISTS price_forecasts (
    date          DATE NOT NULL,
    crop_id       VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    market        VARCHAR(80) NOT NULL,
    p10           NUMERIC(8, 2) NOT NULL,
    p50           NUMERIC(8, 2) NOT NULL,
    p90           NUMERIC(8, 2) NOT NULL,
    model_version VARCHAR(30) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, crop_id, market, model_version)
);

-- 9.4 ML Demand Forecasts (q10, q50, q90)
CREATE TABLE IF NOT EXISTS demand_forecasts (
    date          DATE NOT NULL,
    hub_id        VARCHAR(64) NOT NULL REFERENCES hubs(id) ON DELETE CASCADE,
    crop_id       VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    q10           NUMERIC(10, 2) NOT NULL,
    q50           NUMERIC(10, 2) NOT NULL,
    q90           NUMERIC(10, 2) NOT NULL,
    model_version VARCHAR(30) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, hub_id, crop_id, model_version)
);

-- 9.5 Published Prices (What users see after admin approval)
CREATE TABLE IF NOT EXISTS published_prices (
    date            DATE NOT NULL,
    crop_id         VARCHAR(64) NOT NULL REFERENCES crops(id) ON DELETE CASCADE,
    low             NUMERIC(8, 2) NOT NULL, -- in paise
    high            NUMERIC(8, 2) NOT NULL, -- in paise
    reference       NUMERIC(8, 2) NOT NULL, -- in paise
    overridden      BOOLEAN DEFAULT false,
    override_reason TEXT,
    published_by    VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    published_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (date, crop_id)
);

-- ==============================================================================
-- 10. FINANCIALS & DOUBLE-ENTRY LEDGER
-- ==============================================================================

-- 10.1 Payments
CREATE TABLE IF NOT EXISTS payments (
    id            VARCHAR(64) PRIMARY KEY,
    party_id      VARCHAR(64) NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    direction     payment_direction NOT NULL,
    amount        BIGINT NOT NULL, -- paise
    status        payment_status DEFAULT 'PENDING',
    gateway_ref   VARCHAR(80),
    order_id      VARCHAR(64) REFERENCES orders(id) ON DELETE SET NULL,
    settlement_id VARCHAR(64),
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 10.2 Daily Farmer Settlements
CREATE TABLE IF NOT EXISTS settlements (
    id              VARCHAR(64) PRIMARY KEY,
    farmer_id       VARCHAR(64) NOT NULL REFERENCES farmers(user_id) ON DELETE RESTRICT,
    settle_date     DATE NOT NULL,
    accepted_kg     NUMERIC(10, 2) NOT NULL,
    gross           BIGINT NOT NULL, -- paise
    commission      BIGINT NOT NULL, -- paise
    logistics_share BIGINT NOT NULL, -- paise
    net             BIGINT NOT NULL, -- paise
    status          VARCHAR(15) DEFAULT 'DRAFT',
    approved_by     VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    paid_at         TIMESTAMPTZ,
    CONSTRAINT uq_farmer_settle_date UNIQUE (farmer_id, settle_date)
);

-- 10.3 Double-Entry Ledger Entries
CREATE TABLE IF NOT EXISTS ledger_entries (
    id         BIGSERIAL PRIMARY KEY,
    txn_id     VARCHAR(64) NOT NULL,
    account    VARCHAR(40) NOT NULL, -- 'farmer_payable', 'buyer_receivable', 'commission_income', 'wastage_expense'
    party_id   VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    debit      BIGINT DEFAULT 0,
    credit     BIGINT DEFAULT 0,
    ref_type   VARCHAR(30),
    ref_id     VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 11. PLATFORM, NOTIFICATIONS & AUDIT
-- ==============================================================================

-- 11.1 Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id         VARCHAR(64) PRIMARY KEY,
    user_id    VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
    channel    VARCHAR(10) NOT NULL, -- 'push', 'sms', 'whatsapp'
    template   VARCHAR(60) NOT NULL,
    payload    JSONB,
    status     VARCHAR(10) DEFAULT 'SENT',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11.2 Domain Events
CREATE TABLE IF NOT EXISTS events (
    id         BIGSERIAL PRIMARY KEY,
    type       VARCHAR(60) NOT NULL,
    entity_id  VARCHAR(64),
    payload    JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11.3 Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id         BIGSERIAL PRIMARY KEY,
    user_id    VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    action     VARCHAR(60) NOT NULL,
    entity     VARCHAR(40) NOT NULL,
    entity_id  VARCHAR(64),
    before     JSONB,
    after      JSONB,
    ip         VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11.4 Settings
CREATE TABLE IF NOT EXISTS settings (
    key        VARCHAR(60) PRIMARY KEY,
    value      JSONB NOT NULL,
    updated_by VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11.5 Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id          VARCHAR(64) PRIMARY KEY,
    trip_id     VARCHAR(64) REFERENCES trips(id) ON DELETE SET NULL,
    type        VARCHAR(30) NOT NULL, -- 'BREAKDOWN', 'ACCIDENT', 'DELAY'
    notes       TEXT,
    reported_by VARCHAR(64) REFERENCES users(id) ON DELETE SET NULL,
    resolved    BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- 12. PERFORMANCE INDEXES
-- ==============================================================================

CREATE INDEX IF NOT EXISTS idx_farmers_loc ON farmers USING gist (location);
CREATE INDEX IF NOT EXISTS idx_buyers_loc ON buyers USING gist (location);
CREATE INDEX IF NOT EXISTS idx_hubs_loc ON hubs USING gist (location);
CREATE INDEX IF NOT EXISTS idx_location_pings_loc ON location_pings USING gist (location);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_listings_date ON farmer_listings(listing_date, status);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(delivery_date, status);
CREATE INDEX IF NOT EXISTS idx_trips_driver ON trips(driver_id, status);
CREATE INDEX IF NOT EXISTS idx_stock_ledger_hub_crop ON stock_ledger(hub_id, crop_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transfer_status ON transfer_requests(status);
