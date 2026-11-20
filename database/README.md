# 🗄️ KrishiLink Database Architecture

This directory contains the production database architecture, schema definitions, seed datasets, SQLAlchemy 2.0 models, authentication credentials, and migration tools for the KrishiLink agricultural logistics platform.

It implements the specifications outlined in:
* [`03_ARCHITECTURE.md`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/03_ARCHITECTURE.md)
* [`04_DATABASE_SCHEMA.md`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/04_DATABASE_SCHEMA.md)
* [`05_API_SPEC.md`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/05_API_SPEC.md)

---

## 1. Architecture Overview

KrishiLink operates on a **PostgreSQL 16+ with PostGIS** geospatial database layer, supported by **Redis 7** for realtime pub/sub GPS tracking:

```mermaid
erDiagram
    USERS ||--o| FARMERS : "profile"
    USERS ||--o| BUYERS : "profile"
    USERS ||--o| DRIVERS : "profile"
    USERS ||--o{ HUB_STAFF : "staff assignment"
    HUBS ||--o{ HUB_STAFF : "staffed by"
    HUBS ||--o{ FARMERS : "nearest hub"
    HUBS ||--o{ BUYERS : "delivery hub"
    HUBS ||--o{ DRIVERS : "home hub"
    HUBS ||--o{ HUB_STOCK_STATUS : "three-button state"
    CROPS ||--o{ HUB_STOCK_STATUS : "crop state"
    HUBS ||--o{ STOCK_LEDGER : "audit entry"
    CROPS ||--o{ STOCK_LEDGER : "crop entry"
    FARMERS ||--o{ FARMER_LISTINGS : "declares"
    CROPS ||--o{ FARMER_LISTINGS : "crop listed"
    BUYERS ||--o{ ORDERS : "places"
    ORDERS ||--o{ ORDER_ITEMS : "contains"
    CROPS ||--o{ ORDER_ITEMS : "item crop"
    VEHICLES ||--o{ DRIVERS : "assigned vehicle"
    DRIVERS ||--o{ TRIPS : "executes"
    VEHICLES ||--o{ TRIPS : "driven in"
    TRIPS ||--o{ TRIP_STOPS : "stops"
    TRIP_STOPS ||--o{ PICKUP_RECEIPTS : "recorded at"
    TRIPS ||--o{ LOCATION_PINGS : "GPS pings"
    USERS ||--o{ PAYMENTS : "financial transactions"
    FARMERS ||--o{ SETTLEMENTS : "daily payout"
```

---

## 2. Directory Contents

| File | Description |
|---|---|
| [`01_schema.sql`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/01_schema.sql) | Production PostgreSQL 16+ schema with PostGIS geometry, 14 ENUMs, 35 tables, 1 view, foreign keys, triggers, and spatial GiST indexes. |
| [`seeds/seed_data.sql`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/seeds/seed_data.sql) | Production seed dataset containing all 9 hubs, 11 crops, 4 vehicles, 27 users with bcrypt hashes, trips, and orders. |
| [`CREDENTIALS.md`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/CREDENTIALS.md) | Complete directory of login credentials (phones, passwords, OTPs, roles) for all Farmers, Buyers, Drivers, Admins, and Staff. |
| [`models.py`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/models.py) | Full SQLAlchemy 2.0 ORM declarative models mapping all 35 entities. |
| [`schemas.py`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/schemas.py) | Pydantic v2 models for API request/response validation and authentication tokens. |
| [`auth_utils.py`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/auth_utils.py) | Password security utilities: Bcrypt hashing, verification, and JWT generation & decoding. |
| [`connection.py`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/connection.py) | Database engine session manager supporting both PostgreSQL and SQLite fallback. |
| [`init_db.py`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/init_db.py) | Universal database initialization script that creates tables and populates verified seed data. |
| [`test_db.py`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/database/test_db.py) | Automated test suite verifying schema integrity, credentials, foreign keys, and stock ledger calculations. |

---

## 3. Database Entities (35 Tables + 1 View)

### Domain 1: Identity & Credentials
* **`users`**: Master user table with phone, role, full name, email, language (`kn`/`en`), and **`password_hash`** (bcrypt).
* **`hub_staff`**: Maps staff users to their operational hubs.
* **`farmers`**: Farm location (PostGIS Point), taluk, village, land size, UPI ID, reliability score, and nearest hub reference.
* **`farmer_crop_thresholds`**: Per-crop minimum pickup threshold overrides.
* **`buyers`**: Business name, type (restaurant, caterer, etc.), GSTIN, location, delivery hub, and credit limit in paise.
* **`vehicles`**: Reg number, type (Tata Ace, Bolero, Leyland Dost, Eicher Reefer), payload capacity in kg, ownership.
* **`drivers`**: Licence number, vehicle assignment, home hub reference, on-duty status.

### Domain 2: Hubs & Crops
* **`hubs`**: 1 Central Bengaluru Main Hub (Yeshwanthpur) + 4 Village Mini Hubs (Kolar, Chikkaballapur, Doddaballapur, Hoskote) + 4 City Mini Hubs (Whitefield, HSR, Jayanagar, Malleshwaram).
* **`crops`**: 11 vegetables and herbs with English and Kannada names, organic flags, perishability scores, and default thresholds.

### Domain 3: Stock Management
* **`hub_stock_status`**: Human-facing **three-button status** (`OUT`, `LOW`, `SUFFICIENT`) and system suggestions per hub per crop.
* **`hub_stock_status_history`**: Audit trail of every manual or system status transition.
* **`stock_ledger`**: Double-entry quantity truth recording delta kg for pickups, transfers, wastage, and deliveries.
* **`hub_stock_current`**: Database view calculating real-time sum of available kg per crop per hub.

### Domain 4: Supply & Demand
* **`farmer_listings`**: Pre-harvest and ready produce declarations with cutoff validation.
* **`orders`**: Bulk buyer orders with delivery slots, payment mode (Prepaid/Credit), status, and delivery OTP.
* **`order_items`**: Line items with requested kg, confirmed kg, locked price in paise, and substitutions.

### Domain 5: Logistics & Tracking
* **`trips`**: First Mile, Middle Mile, Last Mile, and Transfer trips with planned vs actual kg and status.
* **`trip_stops`**: Ordered sequence of pickup, hub, and delivery stops with ETAs and completion timestamps.
* **`pickup_receipts`**: Weighed-in receipts recorded by drivers at farms with farmer tap/OTP confirmation.
* **`hub_receipts`**: Second weigh-in at hub to compute variance percentage.
* **`location_pings`**: GPS tracking pings (latitude, longitude, speed, heading, timestamp).
* **`transfer_requests`**: Lateral stock balancing requests between donor and receiver hubs.

### Domain 6: Pricing & ML Forecasts
* **`market_prices`**: Daily raw Agmarknet APMC mandi prices and arrival quantities.
* **`weather_daily`**: Open-Meteo rainfall, temperature, and humidity.
* **`price_forecasts`**: ML p10, p50, p90 price confidence intervals.
* **`demand_forecasts`**: ML q10, q50, q90 demand intervals per hub per crop.
* **`published_prices`**: Published price ranges (low, high, reference in paise) approved by admin.

### Domain 7: Money & Platform
* **`payments`**: Payment records with Razorpay/Cashfree gateway reference and direction (IN/OUT).
* **`settlements`**: Daily farmer payout settlements with gross, commission, and net amounts.
* **`ledger_entries`**: Financial double-entry ledger.
* **`notifications`**: Push, SMS, and WhatsApp alerts.
* **`events`**: Event stream for asynchronous workers.
* **`audit_log`**: Security audit log for sensitive operational actions.
* **`settings`**: Configurable system parameters (cutoffs, tolerances, thresholds).
* **`incidents`**: Vehicle breakdown or route delay incident tracking.

---

## 4. How to Run & Connect

### Option A: Local / Offline Zero-Config (SQLite)
The repository includes an auto-configured SQLite engine that works immediately without installing external servers:
```bash
# 1. Initialize schema and seed credentials
python database/init_db.py

# 2. Run verification tests
python database/test_db.py
```

### Option B: Production / Docker (PostgreSQL 16 + PostGIS)
To run the full PostGIS and Redis stack:
```bash
# 1. Start Docker containers
docker compose -f infra/docker-compose.yml up -d

# 2. Connect via psql
psql -h localhost -p 5432 -U krishi_admin -d krishilink

# 3. Configure environment variable
export DATABASE_URL="postgresql://krishi_admin:krishi_pass_2026@localhost:5432/krishilink"
```

---

## 5. User Credentials Summary

For complete credentials, see [`CREDENTIALS.md`](file:///c:/Users/omkar/OneDrive/Desktop/CP2_DATA/CREDENTIALS.md).

* **Default Password:** `123456`
* **Admin Login:** `9876543204` / `123456` (Anita Rao)
* **Hub Staff Login:** `9876543205` / `123456` (Praveen Nayak - Kolar)
* **Driver Login:** `9876543203` / `123456` (Suresh Kumar - Tata Ace)
* **Farmer Login:** `9876543202` / `123456` (Ramesh Gowda - Kolar)
* **Buyer Login:** `9876543201` / `123456` (Udupi Upahar - Kiran Kumar)
