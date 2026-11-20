"""
Database Verification and Test Suite
Validates schema integrity, foreign keys, BCrypt password authentication,
and domain operations across Farmers, Buyers, Drivers, Admins, Hubs, and Orders.
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.connection import SessionLocal
from database.auth_utils import verify_password, create_access_token, decode_access_token
from database.models import (
    User, Hub, Vehicle, Driver, Farmer, Buyer, Crop,
    HubStockStatus, StockLedger, Order, Trip, TripStop
)

def test_database():
    session = SessionLocal()
    passed = 0
    total = 0

    def assert_check(name: str, condition: bool):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            print(f"  ❌ FAILED: {name}")

    print("\n" + "=" * 70)
    print("🧪 RUNNING KRISHILINK DATABASE VERIFICATION TESTS")
    print("=" * 70)

    try:
        # TEST 1: User Counts & Roles
        print("\n--- Test 1: User Demographics & Roles ---")
        users = session.query(User).all()
        assert_check("At least 27 Users present in database", len(users) >= 27)

        admins = [u for u in users if u.role == "admin"]
        staff = [u for u in users if u.role == "hub_staff"]
        drivers = [u for u in users if u.role == "driver"]
        farmers = [u for u in users if u.role == "farmer"]
        buyers = [u for u in users if u.role == "buyer"]

        assert_check("Seed Admin present (Anita Rao)", any(u.id == "u_admin_1" for u in admins))
        assert_check("Hub Staff present (Praveen, Manjunath)", len(staff) >= 2)
        assert_check("Fleet Drivers present", len(drivers) >= 4)
        assert_check("Farmers present", len(farmers) >= 12)
        assert_check("Bulk Buyers present", len(buyers) >= 8)

        # TEST 2: Credentials and BCrypt Password Validation
        print("\n--- Test 2: Credentials & Password Authentication ---")
        admin_user = session.query(User).filter_by(id="u_admin_1").first()
        driver_user = session.query(User).filter_by(id="u_driver_1").first()
        farmer_user = session.query(User).filter_by(id="u_farmer_1").first()
        buyer_user = session.query(User).filter_by(id="u_buyer_1").first()

        assert_check("Admin password authentication succeeds with '123456'", verify_password("123456", admin_user.password_hash))
        assert_check("Admin password authentication rejects wrong password 'wrongpass'", not verify_password("wrongpass", admin_user.password_hash))
        assert_check("Driver password authentication succeeds with '123456'", verify_password("123456", driver_user.password_hash))
        assert_check("Farmer password authentication succeeds with '123456'", verify_password("123456", farmer_user.password_hash))
        assert_check("Buyer password authentication succeeds with '123456'", verify_password("123456", buyer_user.password_hash))

        # TEST 3: JWT Token Generation & Decoding
        print("\n--- Test 3: JWT Token Lifecycle ---")
        token = create_access_token(admin_user.id, admin_user.role, admin_user.phone)
        payload = decode_access_token(token)
        assert_check("JWT generated and successfully decoded", payload is not None)
        assert_check("JWT payload has correct sub (user_id)", payload.get("sub") == "u_admin_1")
        assert_check("JWT payload has correct role", payload.get("role") == "admin")

        # TEST 4: Profile Relationships (Foreign Keys)
        print("\n--- Test 4: Role Profile Foreign Key Integrity ---")
        farmer1 = session.query(Farmer).filter_by(user_id="u_farmer_1").first()
        assert_check("Farmer profile linked to user: Ramesh Gowda", farmer1 is not None and farmer1.user.name == "Ramesh Gowda")
        assert_check("Farmer has nearest hub configured (Kolar)", farmer1.nearest_hub_id == "h_kolar")

        buyer1 = session.query(Buyer).filter_by(user_id="u_buyer_1").first()
        assert_check("Buyer profile linked to user: Kiran Kumar", buyer1 is not None and "Udupi Upahar" in buyer1.business_name)
        assert_check("Buyer has delivery hub configured (HSR)", buyer1.delivery_hub_id == "h_hsr")

        driver1 = session.query(Driver).filter_by(user_id="u_driver_1").first()
        assert_check("Driver profile linked to vehicle v_1", driver1 is not None and driver1.vehicle_id == "v_1")

        # TEST 5: Hubs, Crops & Stock Matrix
        print("\n--- Test 5: Hubs, Crops & Three-Button Stock Matrix ---")
        hubs_count = session.query(Hub).count()
        crops_count = session.query(Crop).count()
        assert_check("All 9 Hubs exist", hubs_count == 9)
        assert_check("All 11 Crops exist", crops_count == 11)

        hsr_tomato_status = session.query(HubStockStatus).filter_by(hub_id="h_hsr", crop_id="c_tomato").first()
        assert_check("HSR Hub Tomato stock status is LOW with suggested OUT",
                     hsr_tomato_status is not None and hsr_tomato_status.status == "LOW" and hsr_tomato_status.suggested == "OUT")

        main_hub_stock = session.query(StockLedger).filter_by(hub_id="h_main", crop_id="c_tomato").first()
        assert_check("Stock Ledger records positive inflow for Main Hub Tomato (2500 kg)",
                     main_hub_stock is not None and main_hub_stock.delta_kg == 2500.0)

        # TEST 6: Orders and Items
        print("\n--- Test 6: Orders & Order Line Items ---")
        order = session.query(Order).filter_by(id="order_101").first()
        assert_check("Order 101 exists with status OUT_FOR_DELIVERY", order is not None and order.status == "OUT_FOR_DELIVERY")
        assert_check("Order 101 has 2 line items", len(order.items) == 2)
        assert_check("Order 101 delivery OTP matches '4821'", order.delivery_otp == "4821")

        # TEST 7: Trips and Stops
        print("\n--- Test 7: Active Trips & Ordered Stops ---")
        trip = session.query(Trip).filter_by(id="trip_first_mile_1").first()
        assert_check("First Mile Trip exists and is STARTED", trip is not None and trip.status == "STARTED")
        assert_check("Trip has 4 stops ordered by seq", len(trip.stops) == 4 and [s.seq for s in trip.stops] == [1, 2, 3, 4])
        assert_check("Stop 1 is Completed pickup from Ramesh Gowda Farm",
                     trip.stops[0].status == "COMPLETED" and trip.stops[0].farmer_id == "u_farmer_1")

        print("\n" + "=" * 70)
        print(f"📊 TEST RESULTS: {passed}/{total} CHECKS PASSED")
        print("=" * 70)

        if passed == total:
            print("🌟 ALL DATABASE INTEGRITY & AUTH CHECKS PASSED PERFECTLY!\n")
        else:
            print("⚠️ SOME CHECKS FAILED. Please review above.\n")

    finally:
        session.close()

if __name__ == "__main__":
    test_database()
