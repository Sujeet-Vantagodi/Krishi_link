"""
Universal Database Initializer & Seeder
Initializes database tables, creates views, and populates all production seed data
with verified bcrypt password hashes for all 27 platform actors.
Supports both PostgreSQL (Production) and SQLite (Local / Offline).
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, time, timezone

# Add repository root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from database.connection import engine, SessionLocal, Base
from database.auth_utils import hash_password
from database.models import (
    User, Hub, HubStaff, Vehicle, Driver, Farmer, Buyer, Crop,
    FarmerCropThreshold, HubStockStatus, StockLedger, Order, OrderItem,
    Trip, TripStop, PickupReceipt, PublishedPrice, Setting,
    PriceForecast, DemandForecast
)

def run_init():
    print("=" * 70)
    print("🌱 KRISHILINK DATABASE INITIALIZATION")
    print(f"Target Database Engine: {engine.url}")
    print("=" * 70)

    # 1. Create all tables
    print("\n[1/4] Creating all 35 database tables and schema structures...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully.")

    # 2. Open session
    session = SessionLocal()

    try:
        # Check if already seeded
        existing_users = session.query(User).count()
        if existing_users > 0:
            print(f"\nDatabase already contains {existing_users} users. Cleaning and re-seeding...")
            # Delete dependent records in order
            session.query(TripStop).delete()
            session.query(Trip).delete()
            session.query(OrderItem).delete()
            session.query(Order).delete()
            session.query(StockLedger).delete()
            session.query(HubStockStatus).delete()
            session.query(FarmerCropThreshold).delete()
            session.query(PublishedPrice).delete()
            session.query(PriceForecast).delete()
            session.query(DemandForecast).delete()
            session.query(Farmer).delete()
            session.query(Buyer).delete()
            session.query(Driver).delete()
            session.query(HubStaff).delete()
            session.query(User).delete()
            session.query(Crop).delete()
            session.query(Vehicle).delete()
            session.query(Hub).delete()
            session.commit()

        print("\n[2/4] Seeding Infrastructure: Hubs, Crops, and Vehicles...")

        # 9 Hubs
        hubs_data = [
            Hub(id="h_main", name="Bengaluru Main Hub (Yeshwanthpur)", type="main", parent_hub_id=None,
                latitude=13.0285, longitude=77.5400, address="APMC Yard, Yeshwanthpur, Bengaluru 560022",
                capacity_kg=50000.0, has_cold_room=True, active=True),
            Hub(id="h_kolar", name="Kolar Village Mini Hub", type="village", parent_hub_id="h_main",
                latitude=13.1360, longitude=78.1290, address="Mandi Road, Kolar Rural 563101",
                capacity_kg=12000.0, has_cold_room=False, active=True),
            Hub(id="h_chikkaballapur", name="Chikkaballapur Village Mini Hub", type="village", parent_hub_id="h_main",
                latitude=13.4355, longitude=77.7315, address="Near Old Bus Stand, Chikkaballapur 562101",
                capacity_kg=10000.0, has_cold_room=False, active=True),
            Hub(id="h_doddaballapur", name="Doddaballapur Village Mini Hub", type="village", parent_hub_id="h_main",
                latitude=13.2257, longitude=77.5750, address="Industrial Area Main Road, Doddaballapur 561203",
                capacity_kg=8000.0, has_cold_room=False, active=True),
            Hub(id="h_hoskote", name="Hoskote Village Mini Hub", type="village", parent_hub_id="h_main",
                latitude=13.0707, longitude=77.7982, address="National Highway Cross, Hoskote 562114",
                capacity_kg=9000.0, has_cold_room=False, active=True),
            Hub(id="h_whitefield", name="Whitefield City Mini Hub", type="city", parent_hub_id="h_main",
                latitude=12.9698, longitude=77.7500, address="ITPL Main Road, Whitefield, Bengaluru 560066",
                capacity_kg=15000.0, has_cold_room=True, active=True),
            Hub(id="h_hsr", name="HSR Layout City Mini Hub", type="city", parent_hub_id="h_main",
                latitude=12.9116, longitude=77.6389, address="Sector 2, 27th Main, HSR Layout, Bengaluru 560102",
                capacity_kg=15000.0, has_cold_room=True, active=True),
            Hub(id="h_jayanagar", name="Jayanagar City Mini Hub", type="city", parent_hub_id="h_main",
                latitude=12.9308, longitude=77.5838, address="4th Block, 11th Main, Jayanagar, Bengaluru 560011",
                capacity_kg=12000.0, has_cold_room=True, active=True),
            Hub(id="h_malleshwaram", name="Malleshwaram City Mini Hub", type="city", parent_hub_id="h_main",
                latitude=13.0035, longitude=77.5647, address="8th Cross, Sampige Road, Malleshwaram 560003",
                capacity_kg=10000.0, has_cold_room=True, active=True),
        ]
        session.add_all(hubs_data)
        session.commit()

        # 4 Vehicles
        vehicles_data = [
            Vehicle(id="v_1", reg_no="KA 01 AB 1234", type="Tata Ace (Chota Hathi)", capacity_kg=1000.0, ownership="rent", active=True),
            Vehicle(id="v_2", reg_no="KA 04 C 5678", type="Mahindra Bolero Maxi Truck", capacity_kg=1500.0, ownership="rent", active=True),
            Vehicle(id="v_3", reg_no="KA 03 D 9012", type="Ashok Leyland Dost", capacity_kg=1250.0, ownership="own", active=True),
            Vehicle(id="v_4", reg_no="KA 51 E 3456", type="Eicher Pro 2049 (Reefer)", capacity_kg=2500.0, ownership="rent", active=True),
        ]
        session.add_all(vehicles_data)

        # 11 Crops
        crops_data = [
            Crop(id="c_tomato", slug="tomato", name_en="Tomato", name_kn="ಟೊಮೆಟೊ", category="fruit_veg", is_organic=False,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=96, shelf_life_days=4, perishability=4, image_emoji="🍅"),
            Crop(id="c_tomato_org", slug="tomato-organic", name_en="Tomato (Organic)", name_kn="ಟೊಮೆಟೊ (ಸಾವಯವ)", category="fruit_veg", is_organic=True,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=96, shelf_life_days=4, perishability=4, image_emoji="🍅"),
            Crop(id="c_onion", slug="onion", name_en="Onion", name_kn="ಈರುಳ್ಳಿ", category="roots", is_organic=False,
                 min_order_kg=25.0, default_min_kg=30.0, shelf_life_hours=480, shelf_life_days=20, perishability=2, image_emoji="🧅"),
            Crop(id="c_potato", slug="potato", name_en="Potato", name_kn="ಆಲೂಗಡ್ಡೆ", category="roots", is_organic=False,
                 min_order_kg=25.0, default_min_kg=30.0, shelf_life_hours=720, shelf_life_days=30, perishability=1, image_emoji="🥔"),
            Crop(id="c_carrot", slug="carrot", name_en="Carrot", name_kn="ಗಜ್ಜರಿ", category="roots", is_organic=False,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=168, shelf_life_days=7, perishability=3, image_emoji="🥕"),
            Crop(id="c_beans", slug="french-beans", name_en="French Beans", name_kn="ಬೀನ್ಸ್", category="fruit_veg", is_organic=False,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=120, shelf_life_days=5, perishability=4, image_emoji="🫘"),
            Crop(id="c_cabbage", slug="cabbage", name_en="Cabbage", name_kn="ಎಲೆಕೋಸು", category="leafy", is_organic=False,
                 min_order_kg=15.0, default_min_kg=25.0, shelf_life_hours=192, shelf_life_days=8, perishability=3, image_emoji="🥬"),
            Crop(id="c_cauliflower", slug="cauliflower", name_en="Cauliflower", name_kn="ಹೂಕೋಸು", category="fruit_veg", is_organic=False,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=120, shelf_life_days=5, perishability=4, image_emoji="🥦"),
            Crop(id="c_brinjal", slug="brinjal", name_en="Brinjal (Eggplant)", name_kn="ಬದನೆಕಾಯಿ", category="fruit_veg", is_organic=False,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=144, shelf_life_days=6, perishability=3, image_emoji="🍆"),
            Crop(id="c_green_chilli", slug="green-chilli", name_en="Green Chilli", name_kn="ಹಸಿರು ಮೆಣಸಿನಕಾಯಿ", category="herbs", is_organic=False,
                 min_order_kg=5.0, default_min_kg=10.0, shelf_life_hours=168, shelf_life_days=7, perishability=3, image_emoji="🌶️"),
            Crop(id="c_capsicum", slug="capsicum", name_en="Capsicum (Bell Pepper)", name_kn="ದೊಡ್ಡ ಮೆಣಸಿನಕಾಯಿ", category="fruit_veg", is_organic=False,
                 min_order_kg=10.0, default_min_kg=20.0, shelf_life_hours=144, shelf_life_days=6, perishability=4, image_emoji="🫑"),
        ]
        session.add_all(crops_data)
        session.commit()
        print(f"✓ Seeded 9 Hubs, 4 Vehicles, and 11 Crops.")

        # 3. Users and Credentials
        print("\n[3/4] Seeding Users and Generating Bcrypt Password Hashes...")
        default_pwd_hash = hash_password("123456")

        users_data = [
            # Admin
            User(id="u_admin_1", phone="+919876543204", role="admin", name="Anita Rao (Ops Tower)",
                 email="anita.admin@krishilink.in", password_hash=default_pwd_hash, language="en"),
            # Hub Staff
            User(id="u_staff_1", phone="+919876543205", role="hub_staff", name="Praveen Nayak",
                 email="praveen.staff@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_staff_2", phone="+919876543206", role="hub_staff", name="Manjunath Swamy",
                 email="manjunath.staff@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            # Drivers
            User(id="u_driver_1", phone="+919876543203", role="driver", name="Suresh Kumar",
                 email="suresh.driver@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_driver_2", phone="+919876543207", role="driver", name="Ramesh B",
                 email="ramesh.driver@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_driver_3", phone="+919876543208", role="driver", name="Venkatesh N",
                 email="venkatesh.driver@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_driver_4", phone="+919876543209", role="driver", name="Anand Gowda",
                 email="anand.driver@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            # 12 Farmers
            User(id="u_farmer_1", phone="+919876543202", role="farmer", name="Ramesh Gowda",
                 email="ramesh.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_2", phone="+919876543211", role="farmer", name="Muniyappa K",
                 email="muniyappa.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_3", phone="+919876543212", role="farmer", name="Narayanappa",
                 email="narayanappa.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_4", phone="+919876543213", role="farmer", name="Krishnappa Reddy",
                 email="krishnappa.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_5", phone="+919876543214", role="farmer", name="Shivalingaiah",
                 email="shivalingaiah.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_6", phone="+919876543215", role="farmer", name="Venkataramanappa",
                 email="venkataramana.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_7", phone="+919876543216", role="farmer", name="Anjanappa",
                 email="anjanappa.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_8", phone="+919876543217", role="farmer", name="Lakshmamma",
                 email="lakshmamma.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_9", phone="+919876543218", role="farmer", name="Chennappa",
                 email="chennappa.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_10", phone="+919876543219", role="farmer", name="Byre Gowda",
                 email="byregowda.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_11", phone="+919876543220", role="farmer", name="Gopalappa",
                 email="gopalappa.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            User(id="u_farmer_12", phone="+919876543221", role="farmer", name="Srinivas Murthy",
                 email="srinivas.farmer@krishilink.in", password_hash=default_pwd_hash, language="kn"),
            # 8 Buyers
            User(id="u_buyer_1", phone="+919876543201", role="buyer", name="Kiran Kumar (Udupi Upahar)",
                 email="kiran.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_2", phone="+919876543231", role="buyer", name="Nagarjuna Restaurant Indiranagar",
                 email="nagarjuna.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_3", phone="+919876543232", role="buyer", name="A2B Caterers & Sweets BTM",
                 email="a2b.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_4", phone="+919876543233", role="buyer", name="Pai Comforts Student Hostel",
                 email="paicomforts.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_5", phone="+919876543234", role="buyer", name="SLV Grand Veg Banashankari",
                 email="slvgrand.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_6", phone="+919876543235", role="buyer", name="Mavalli Tiffin Room (MTR Lalbagh)",
                 email="mtr.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_7", phone="+919876543236", role="buyer", name="Meghana Foods Koramangala",
                 email="meghana.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
            User(id="u_buyer_8", phone="+919876543237", role="buyer", name="Bangalore Central Wholesale Market",
                 email="centralmarket.buyer@krishilink.in", password_hash=default_pwd_hash, language="en"),
        ]
        session.add_all(users_data)
        session.commit()

        # Hub Staff Mappings
        session.add_all([
            HubStaff(user_id="u_staff_1", hub_id="h_kolar"),
            HubStaff(user_id="u_staff_2", hub_id="h_main"),
        ])

        # Drivers Profiles
        session.add_all([
            Driver(user_id="u_driver_1", licence_no="KA01-2018-0098765", vehicle_id="v_1", home_hub_id="h_kolar", on_duty=True),
            Driver(user_id="u_driver_2", licence_no="KA04-2016-0043210", vehicle_id="v_2", home_hub_id="h_main", on_duty=True),
            Driver(user_id="u_driver_3", licence_no="KA03-2019-0012345", vehicle_id="v_3", home_hub_id="h_hsr", on_duty=True),
            Driver(user_id="u_driver_4", licence_no="KA51-2015-0077889", vehicle_id="v_4", home_hub_id="h_chikkaballapur", on_duty=False),
        ])

        # Farmers Profiles
        farmers_data = [
            Farmer(user_id="u_farmer_1", village="Vemgal", taluk="Kolar", district="Kolar",
                   latitude=13.1672, longitude=78.0821, nearest_hub_id="h_kolar", land_acres=2.5,
                   default_min_kg=30.0, upi_id="rameshgowda@oksbi", reliability_score=4.9, approved=True),
            Farmer(user_id="u_farmer_2", village="Sugatur", taluk="Kolar", district="Kolar",
                   latitude=13.1189, longitude=78.1480, nearest_hub_id="h_kolar", land_acres=1.8,
                   default_min_kg=20.0, upi_id="muniyappa@okaxis", reliability_score=4.8, approved=True),
            Farmer(user_id="u_farmer_3", village="Narasapura", taluk="Kolar", district="Kolar",
                   latitude=13.1495, longitude=78.0163, nearest_hub_id="h_kolar", land_acres=3.0,
                   default_min_kg=40.0, upi_id="narayanappa@oksbi", reliability_score=4.7, approved=True),
            Farmer(user_id="u_farmer_4", village="Shidlaghatta Cross", taluk="Chikkaballapur", district="Chikkaballapur",
                   latitude=13.4120, longitude=77.7650, nearest_hub_id="h_chikkaballapur", land_acres=2.0,
                   default_min_kg=25.0, upi_id="krishnappa@okicici", reliability_score=4.9, approved=True),
            Farmer(user_id="u_farmer_5", village="Gauribidanur Road", taluk="Chikkaballapur", district="Chikkaballapur",
                   latitude=13.4560, longitude=77.7120, nearest_hub_id="h_chikkaballapur", land_acres=2.2,
                   default_min_kg=20.0, upi_id="shivaling@oksbi", reliability_score=4.6, approved=True),
            Farmer(user_id="u_farmer_6", village="Bagepalli Cross", taluk="Chikkaballapur", district="Chikkaballapur",
                   latitude=13.4890, longitude=77.7450, nearest_hub_id="h_chikkaballapur", land_acres=1.5,
                   default_min_kg=20.0, upi_id="venkat@okaxis", reliability_score=4.5, approved=True),
            Farmer(user_id="u_farmer_7", village="Tubagere", taluk="Doddaballapur", district="Bangalore Rural",
                   latitude=13.2680, longitude=77.5340, nearest_hub_id="h_doddaballapur", land_acres=3.5,
                   default_min_kg=35.0, upi_id="anjanappa@oksbi", reliability_score=5.0, approved=True),
            Farmer(user_id="u_farmer_8", village="Sasalu", taluk="Doddaballapur", district="Bangalore Rural",
                   latitude=13.2950, longitude=77.5890, nearest_hub_id="h_doddaballapur", land_acres=1.2,
                   default_min_kg=15.0, upi_id="lakshmamma@okicici", reliability_score=4.7, approved=True),
            Farmer(user_id="u_farmer_9", village="Kasaba", taluk="Doddaballapur", district="Bangalore Rural",
                   latitude=13.2120, longitude=77.5620, nearest_hub_id="h_doddaballapur", land_acres=2.8,
                   default_min_kg=30.0, upi_id="chennappa@oksbi", reliability_score=4.8, approved=True),
            Farmer(user_id="u_farmer_10", village="Sulibele", taluk="Hoskote", district="Bangalore Rural",
                   latitude=13.1250, longitude=77.8240, nearest_hub_id="h_hoskote", land_acres=2.0,
                   default_min_kg=25.0, upi_id="byregowda@okaxis", reliability_score=4.9, approved=True),
            Farmer(user_id="u_farmer_11", village="Anugondanahalli", taluk="Hoskote", district="Bangalore Rural",
                   latitude=13.0450, longitude=77.8420, nearest_hub_id="h_hoskote", land_acres=4.0,
                   default_min_kg=40.0, upi_id="gopalappa@oksbi", reliability_score=4.9, approved=True),
            Farmer(user_id="u_farmer_12", village="Jadigenahalli", taluk="Hoskote", district="Bangalore Rural",
                   latitude=13.0820, longitude=77.8710, nearest_hub_id="h_hoskote", land_acres=2.4,
                   default_min_kg=20.0, upi_id="srinivas@okicici", reliability_score=4.7, approved=True),
        ]
        session.add_all(farmers_data)

        # Buyers Profiles
        buyers_data = [
            Buyer(user_id="u_buyer_1", business_name="Udupi Upahar Veg Restaurant", business_type="restaurant",
                  gstin="29ABCDE1234F1Z5", address="14th Main, HSR Layout Sector 4, Bengaluru 560102",
                  latitude=12.9116, longitude=77.6389, delivery_hub_id="h_hsr", credit_limit=15000000,
                  credit_days=7, credit_due=4250000, approved=True),
            Buyer(user_id="u_buyer_2", business_name="Nagarjuna Restaurant Indiranagar", business_type="restaurant",
                  gstin="29BCDEF2345G2Z6", address="100ft Road, HAL 2nd Stage, Indiranagar, Bengaluru 560038",
                  latitude=12.9719, longitude=77.6412, delivery_hub_id="h_whitefield", credit_limit=25000000,
                  credit_days=15, credit_due=11000000, approved=True),
            Buyer(user_id="u_buyer_3", business_name="A2B Caterers & Sweets BTM", business_type="caterer",
                  gstin="29CDEFG3456H3Z7", address="Outer Ring Road, BTM 2nd Stage, Bengaluru 560076",
                  latitude=12.9166, longitude=77.6101, delivery_hub_id="h_hsr", credit_limit=30000000,
                  credit_days=10, credit_due=0, approved=True),
            Buyer(user_id="u_buyer_4", business_name="Pai Comforts Student Hostel", business_type="hostel",
                  gstin="29DEFGH4567J4Z8", address="Koramangala 5th Block, Bengaluru 560095",
                  latitude=12.9352, longitude=77.6245, delivery_hub_id="h_hsr", credit_limit=10000000,
                  credit_days=7, credit_due=3500000, approved=True),
            Buyer(user_id="u_buyer_5", business_name="SLV Grand Veg Banashankari", business_type="restaurant",
                  gstin=None, address="80 Feet Road, 3rd Stage, Banashankari, Bengaluru 560085",
                  latitude=12.9254, longitude=77.5468, delivery_hub_id="h_jayanagar", credit_limit=8000000,
                  credit_days=5, credit_due=1200000, approved=True),
            Buyer(user_id="u_buyer_6", business_name="Mavalli Tiffin Room (MTR Lalbagh)", business_type="restaurant",
                  gstin=None, address="14 Lalbagh Road, Mavalli, Bengaluru 560004",
                  latitude=12.9553, longitude=77.5855, delivery_hub_id="h_jayanagar", credit_limit=50000000,
                  credit_days=15, credit_due=0, approved=True),
            Buyer(user_id="u_buyer_7", business_name="Meghana Foods Koramangala", business_type="restaurant",
                  gstin=None, address="Koramangala 4th Block, 80 Feet Road, Bengaluru 560034",
                  latitude=12.9325, longitude=77.6310, delivery_hub_id="h_hsr", credit_limit=20000000,
                  credit_days=7, credit_due=8900000, approved=True),
            Buyer(user_id="u_buyer_8", business_name="Bangalore Central Wholesale Market", business_type="wholesaler",
                  gstin=None, address="K.R. Market Wholesale Yard, Bengaluru 560002",
                  latitude=12.9642, longitude=77.5768, delivery_hub_id="h_main", credit_limit=100000000,
                  credit_days=30, credit_due=24500000, approved=True),
        ]
        session.add_all(buyers_data)
        session.commit()
        print(f"✓ Seeded 27 Users with BCrypt Password Credentials and Role Profiles.")

        # 4. Stock & Operational Records
        print("\n[4/4] Seeding Stock Matrix, Published Prices, Trips, and Orders...")
        
        # Published Prices
        published_prices_data = [
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_tomato", low=2200, high=3000, reference=2600, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_tomato_org", low=3200, high=4200, reference=3700, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_onion", low=2800, high=3400, reference=3100, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_potato", low=2400, high=2900, reference=2650, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_carrot", low=3500, high=4500, reference=4000, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_beans", low=4000, high=5500, reference=4800, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_cabbage", low=1800, high=2400, reference=2100, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_cauliflower", low=2600, high=3600, reference=3100, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_brinjal", low=2500, high=3500, reference=3000, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_green_chilli", low=5000, high=7000, reference=6000, published_by="u_admin_1"),
            PublishedPrice(date=date(2026, 11, 20), crop_id="c_capsicum", low=4500, high=6000, reference=5200, published_by="u_admin_1"),
        ]
        session.add_all(published_prices_data)

        # Stock Status Matrix
        stock_status_data = [
            HubStockStatus(hub_id="h_hsr", crop_id="c_tomato", status="LOW", suggested="OUT", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_hsr", crop_id="c_onion", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_hsr", crop_id="c_potato", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_whitefield", crop_id="c_beans", status="OUT", suggested="OUT", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_whitefield", crop_id="c_tomato", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_jayanagar", crop_id="c_onion", status="LOW", suggested="LOW", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_jayanagar", crop_id="c_tomato", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_malleshwaram", crop_id="c_capsicum", status="OUT", suggested="LOW", set_by="u_admin_1"),
            HubStockStatus(hub_id="h_kolar", crop_id="c_tomato", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_staff_1"),
            HubStockStatus(hub_id="h_kolar", crop_id="c_beans", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_staff_1"),
            HubStockStatus(hub_id="h_main", crop_id="c_tomato", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_staff_2"),
            HubStockStatus(hub_id="h_main", crop_id="c_onion", status="SUFFICIENT", suggested="SUFFICIENT", set_by="u_staff_2"),
        ]
        session.add_all(stock_status_data)

        # Stock Ledger
        ledger_data = [
            StockLedger(hub_id="h_main", crop_id="c_tomato", delta_kg=2500.0, reason="PICKUP", ref_type="initial_seed", created_by="u_staff_2"),
            StockLedger(hub_id="h_main", crop_id="c_onion", delta_kg=4200.0, reason="PICKUP", ref_type="initial_seed", created_by="u_staff_2"),
            StockLedger(hub_id="h_main", crop_id="c_potato", delta_kg=3800.0, reason="PICKUP", ref_type="initial_seed", created_by="u_staff_2"),
            StockLedger(hub_id="h_kolar", crop_id="c_tomato", delta_kg=1200.0, reason="PICKUP", ref_type="initial_seed", created_by="u_staff_1"),
            StockLedger(hub_id="h_kolar", crop_id="c_beans", delta_kg=650.0, reason="PICKUP", ref_type="initial_seed", created_by="u_staff_1"),
            StockLedger(hub_id="h_hsr", crop_id="c_tomato", delta_kg=120.0, reason="TRANSFER_IN", ref_type="initial_seed", created_by="u_admin_1"),
            StockLedger(hub_id="h_hsr", crop_id="c_onion", delta_kg=850.0, reason="TRANSFER_IN", ref_type="initial_seed", created_by="u_admin_1"),
        ]
        session.add_all(ledger_data)

        # Sample Orders
        order1 = Order(id="order_101", buyer_id="u_buyer_1", delivery_hub_id="h_hsr",
                       delivery_date=date(2026, 11, 20), slot="07:00-08:00", status="OUT_FOR_DELIVERY",
                       subtotal=183000, delivery_fee=5000, total=188000, payment_mode="PREPAID",
                       payment_status="SUCCESS", delivery_otp="4821",
                       address="Udupi Upahar, 14th Main, HSR Layout Sector 4, Bengaluru")
        order2 = Order(id="order_102", buyer_id="u_buyer_2", delivery_hub_id="h_whitefield",
                       delivery_date=date(2026, 11, 20), slot="07:30-08:30", status="CONFIRMED",
                       subtotal=245000, delivery_fee=5000, total=250000, payment_mode="CREDIT",
                       payment_status="PENDING", delivery_otp="7192",
                       address="Nagarjuna Restaurant, 100ft Road, Indiranagar, Bengaluru")
        session.add_all([order1, order2])

        session.add_all([
            OrderItem(id="oi_101_1", order_id="order_101", crop_id="c_tomato", qty_kg=50.0, confirmed_kg=50.0, delivered_kg=50.0, price_per_kg_locked=2600, note="FULL"),
            OrderItem(id="oi_101_2", order_id="order_101", crop_id="c_onion", qty_kg=25.0, confirmed_kg=25.0, delivered_kg=25.0, price_per_kg_locked=3100, note="FULL"),
            OrderItem(id="oi_102_1", order_id="order_102", crop_id="c_beans", qty_kg=30.0, confirmed_kg=20.0, delivered_kg=0.0, price_per_kg_locked=4800, note="PARTIAL"),
            OrderItem(id="oi_102_2", order_id="order_102", crop_id="c_carrot", qty_kg=25.0, confirmed_kg=25.0, delivered_kg=0.0, price_per_kg_locked=4000, note="FULL"),
        ])

        # Sample Trips & Stops
        trip1 = Trip(id="trip_first_mile_1", type="FIRST_MILE", status="STARTED",
                     driver_id="u_driver_1", vehicle_id="v_1", origin_hub_id="h_kolar", dest_hub_id="h_kolar",
                     assigned_by="u_admin_1", date=date(2026, 11, 20),
                     planned_start=datetime(2026, 11, 20, 4, 0, 0, tzinfo=timezone.utc),
                     planned_km=48.5, planned_minutes=120, total_planned_kg=840.0, total_actual_kg=520.0)
        trip2 = Trip(id="trip_last_mile_1", type="LAST_MILE", status="STARTED",
                     driver_id="u_driver_3", vehicle_id="v_3", origin_hub_id="h_hsr", dest_hub_id="h_hsr",
                     assigned_by="u_admin_1", date=date(2026, 11, 20),
                     planned_start=datetime(2026, 11, 20, 6, 30, 0, tzinfo=timezone.utc),
                     planned_km=22.0, planned_minutes=75, total_planned_kg=450.0, total_actual_kg=180.0)
        session.add_all([trip1, trip2])

        stops = [
            TripStop(id="stop_1_1", trip_id="trip_first_mile_1", seq=1, type="PICKUP", status="COMPLETED",
                     farmer_id="u_farmer_1", name="Ramesh Gowda Farm", address="Vemgal Village, Kolar",
                     phone="+919876543202", latitude=13.1672, longitude=78.0821, expected_kg=200.0, actual_kg=210.0, eta="04:20"),
            TripStop(id="stop_1_2", trip_id="trip_first_mile_1", seq=2, type="PICKUP", status="COMPLETED",
                     farmer_id="u_farmer_2", name="Muniyappa Farm", address="Sugatur Village, Kolar",
                     phone="+919876543211", latitude=13.1189, longitude=78.1480, expected_kg=310.0, actual_kg=310.0, eta="04:55"),
            TripStop(id="stop_1_3", trip_id="trip_first_mile_1", seq=3, type="PICKUP", status="EN_ROUTE",
                     farmer_id="u_farmer_3", name="Narayanappa Farm", address="Narasapura, Kolar",
                     phone="+919876543212", latitude=13.1495, longitude=78.0163, expected_kg=330.0, actual_kg=0.0, eta="05:40"),
            TripStop(id="stop_1_4", trip_id="trip_first_mile_1", seq=4, type="HUB", status="PLANNED",
                     hub_id="h_kolar", name="Kolar Village Mini Hub", address="Mandi Road, Kolar",
                     phone="+919876543205", latitude=13.1360, longitude=78.1290, expected_kg=0.0, actual_kg=0.0, eta="06:15"),
            TripStop(id="stop_2_1", trip_id="trip_last_mile_1", seq=1, type="DELIVERY", status="EN_ROUTE",
                     buyer_order_id="order_101", name="Udupi Upahar Veg Restaurant",
                     address="14th Main, HSR Layout Sector 4, Bengaluru", phone="+919876543201",
                     latitude=12.9116, longitude=77.6389, expected_kg=75.0, actual_kg=0.0, eta="07:15"),
        ]
        session.add_all(stops)

        # Settings
        session.add(Setting(key="platform_config", value={
            "listing_cutoff_time": "18:00",
            "order_cutoff_time": "20:00",
            "min_route_payload_kg": 150,
            "max_variance_percent": 2.0
        }, updated_by="u_admin_1"))

        session.commit()
        print("✓ Seeded Stock Matrix, Published Prices, Trips, Stops, Orders, and Settings.")

        print("\n" + "=" * 70)
        print("🎉 KRISHILINK DATABASE INITIALIZATION COMPLETE!")
        print("=" * 70)
        print(f"Total Users: {session.query(User).count()} (1 Admin, 2 Hub Staff, 4 Drivers, 12 Farmers, 8 Buyers)")
        print(f"Total Hubs: {session.query(Hub).count()} (1 Central Main Hub + 4 Village Mini Hubs + 4 City Mini Hubs)")
        print(f"Total Crops: {session.query(Crop).count()} Vegetables & Herbs")
        print(f"Total Vehicles: {session.query(Vehicle).count()} Transport Fleet")
        print(f"Default Password for all seed credentials: '123456'")
        print("=" * 70)

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR during database initialization: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    run_init()
