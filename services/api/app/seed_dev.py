"""Idempotently seed the dedicated, fictional KrishiLink SQLite demo database."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import *  # noqa: F403 - convenient complete model registry for demo provisioning

DEMO_DB = Path(__file__).resolve().parents[1] / "krishilink_demo.db"
PHONES = {
    UserRole.FARMER: ["+919999001001", "+919999001002", "+919999001003"],
    UserRole.BUYER: ["+919999002001", "+919999002002", "+919999002003"],
    UserRole.DRIVER: ["+919999003001", "+919999003002", "+919999003003"],
    UserRole.HUB_STAFF: ["+919999004001", "+919999004002"],
    UserRole.ADMIN: ["+919999005001"],
    UserRole.SUPER_ADMIN: ["+919999006001"],
}


def require_demo_database() -> None:
    url = make_url(settings.DATABASE_URL)
    configured = Path(url.database or "").resolve()
    if not settings.is_development or not settings.ENABLE_DEMO_MODE or url.drivername != "sqlite+pysqlite" or configured != DEMO_DB.resolve():
        raise SystemExit(f"Refusing demo seed. Set development/demo mode and DATABASE_URL to exactly {DEMO_DB}")


def seed() -> dict[str, str]:
    require_demo_database()
    Base.metadata.create_all(bind=engine)
    today = date.today()
    names = {
        UserRole.FARMER: ["Lakshmi Gowda", "Ravi Kumar", "Suma Reddy"],
        UserRole.BUYER: ["Mysuru Meals", "Bengaluru Fresh Kitchen", "Namma Cafe"],
        UserRole.DRIVER: ["Manjunath H.", "Shiva Prasad", "Farzana Banu"],
        UserRole.HUB_STAFF: ["Geetha N.", "Prakash B."],
        UserRole.ADMIN: ["Kavya Rao"], UserRole.SUPER_ADMIN: ["Krishna Murthy"],
    }
    with SessionLocal.begin() as db:
        users: dict[UserRole, list[User]] = {}
        for role, phones in PHONES.items():
            users[role] = []
            for index, phone in enumerate(phones):
                user = db.scalar(select(User).where(User.phone == phone))
                if user is not None and user.role != role:
                    raise RuntimeError(f"Demo identity {phone} already has a different role")
                if user is None:
                    user = User(phone=phone, role=role, name=names[role][index], language="en")
                    db.add(user)
                    db.flush()
                users[role].append(user)

        def hub(name: str, kind: HubType, lat: float, lng: float, address: str, parent=None):
            row = db.scalar(select(Hub).where(Hub.name == name))
            if row is None:
                row = Hub(name=name, type=kind, location={"lat": lat, "lng": lng}, address=address, capacity_kg=20000, active=True, parent_hub_id=parent)
                db.add(row)
                db.flush()
            return row

        central = hub("KrishiLink Bengaluru Central Hub", HubType.MAIN, 12.9716, 77.5946, "Yeshwanthpur, Bengaluru")
        village_a = hub("Kolar Vemgal Collection Hub", HubType.VILLAGE, 13.136, 78.129, "Vemgal, Kolar", central.id)
        village_b = hub("Chikkaballapur Village Hub", HubType.VILLAGE, 13.4355, 77.7315, "Chikkaballapur", central.id)
        city_a = hub("Whitefield Distribution Hub", HubType.CITY, 12.9698, 77.75, "Whitefield, Bengaluru", central.id)
        city_b = hub("Electronic City Distribution Hub", HubType.CITY, 12.8452, 77.6602, "Electronic City, Bengaluru", central.id)

        crops = []
        for slug, en, kn, minimum, category, shelf_hours in [
            ("demo-tomato", "Tomato", "ಟೊಮೇಟೊ", 5, "fruit_veg", 96),
            ("demo-onion", "Onion", "ಈರುಳ್ಳಿ", 10, "roots", 336),
            ("demo-ragi", "Ragi", "ರಾಗಿ", 5, "fruit_veg", 720),
        ]:
            crop = db.scalar(select(Crop).where(Crop.slug == slug))
            if crop is None:
                crop = Crop(
                    slug=slug, name_en=en, name_kn=kn, category=category,
                    shelf_life_hours=shelf_hours, min_order_kg=1, default_min_kg=minimum, active=True,
                )
                db.add(crop)
                db.flush()
            crops.append(crop)
            if db.scalar(select(PublishedPrice).where(PublishedPrice.date == today, PublishedPrice.crop_id == crop.id)) is None:
                db.add(PublishedPrice(date=today, crop_id=crop.id, low=20, high=40, reference=30, published_by=users[UserRole.ADMIN][0].id))

        farmers, buyers, drivers = users[UserRole.FARMER], users[UserRole.BUYER], users[UserRole.DRIVER]
        for i, farmer_user in enumerate(farmers):
            if db.get(Farmer, farmer_user.id) is None:
                db.add(Farmer(user_id=farmer_user.id, village=["Vemgal", "Nandi", "Devanahalli"][i], taluk=["Kolar", "Chikkaballapur", "Devanahalli"][i], district="Karnataka", nearest_hub_id=[village_a.id, village_b.id, village_a.id][i], default_min_kg=5, approved=True))
            listing = db.scalar(select(FarmerListing).where(FarmerListing.farmer_id == farmer_user.id, FarmerListing.crop_id == crops[i].id, FarmerListing.listing_date == today))
            if listing is None:
                db.add(FarmerListing(farmer_id=farmer_user.id, crop_id=crops[i].id, listing_date=today, est_kg=75 + i * 10, status=ListingStatus.ELIGIBLE, min_kg_applied=5))
            settlement = db.scalar(select(Settlement).where(Settlement.farmer_id == farmer_user.id, Settlement.settle_date == today))
            if settlement is None:
                db.add(Settlement(farmer_id=farmer_user.id, settle_date=today, accepted_kg=20, gross=60000, commission=3000, logistics_share=1800, net=55200, status="DRAFT"))
        for i, buyer_user in enumerate(buyers):
            if db.get(Buyer, buyer_user.id) is None:
                db.add(Buyer(user_id=buyer_user.id, business_name=names[UserRole.BUYER][i], business_type="restaurant", address="Bengaluru, Karnataka", delivery_hub_id=[city_a.id, city_b.id, central.id][i], approved=True))

        vehicles = []
        for index, reg in enumerate(["KA-DEMO-101", "KA-DEMO-202", "KA-DEMO-303"]):
            vehicle = db.scalar(select(Vehicle).where(Vehicle.reg_no == reg))
            if vehicle is None:
                vehicle = Vehicle(reg_no=reg, type="Demo goods carrier", capacity_kg=1000, ownership=VehicleOwnership.OWN, active=True)
                db.add(vehicle)
                db.flush()
            vehicles.append(vehicle)
            if db.get(Driver, drivers[index].id) is None:
                db.add(Driver(user_id=drivers[index].id, licence_no=f"DEMO-LIC-{index+1:03}", vehicle_id=vehicle.id, home_hub_id=[village_a.id, village_b.id, central.id][index], on_duty=True))
        staff_users = users[UserRole.HUB_STAFF]
        for staff_user, assigned_hub in [(staff_users[0], central), (staff_users[1], city_a)]:
            if db.get(HubStaff, (staff_user.id, assigned_hub.id)) is None:
                db.add(HubStaff(user_id=staff_user.id, hub_id=assigned_hub.id))

        # Inventory is introduced only as a recorded opening balance; farmer estimates remain listings.
        for stock_hub in [central, village_a, city_a, city_b]:
            for crop in crops:
                if not db.scalar(select(StockLedger).where(StockLedger.hub_id == stock_hub.id, StockLedger.crop_id == crop.id, StockLedger.ref_type == "demo_opening")):
                    db.add(StockLedger(hub_id=stock_hub.id, crop_id=crop.id, delta_kg=120, reason=LedgerReason.ADJUSTMENT, ref_type="demo_opening", ref_id=stock_hub.id, created_by=users[UserRole.ADMIN][0].id))

        # Seed an in-progress pickup with a verifiable receipt-to-listing lineage.
        admin = users[UserRole.ADMIN][0]
        pickup_listing = db.scalar(select(FarmerListing).where(FarmerListing.farmer_id == farmers[0].id, FarmerListing.crop_id == crops[0].id, FarmerListing.listing_date == today))
        pickup_trip = db.scalar(select(Trip).where(Trip.assigned_by == admin.id, Trip.type == TripType.FIRST_MILE, Trip.origin_hub_id == village_a.id, Trip.dest_hub_id == central.id))
        if pickup_trip is None:
            pickup_trip = Trip(type=TripType.FIRST_MILE, status=TripStatus.CLOSED, driver_id=drivers[0].id, vehicle_id=vehicles[0].id, origin_hub_id=village_a.id, dest_hub_id=central.id, assigned_by=admin.id, planned_start=datetime.now(timezone.utc), started_at=datetime.now(timezone.utc), ended_at=datetime.now(timezone.utc))
            db.add(pickup_trip)
            db.flush()
            pickup_stop = TripStop(trip_id=pickup_trip.id, seq=1, type=StopType.PICKUP, status=StopStatus.COMPLETED, farmer_id=farmers[0].id, listing_id=pickup_listing.id if pickup_listing else None, location={"lat": 13.136, "lng": 78.129}, completed_at=datetime.now(timezone.utc))
            db.add(pickup_stop)
            db.flush()
            if pickup_listing:
                db.add(PickupReceipt(trip_stop_id=pickup_stop.id, listing_id=pickup_listing.id, crop_id=crops[0].id, kg_received=20, grade=Grade.A, farmer_confirmed=True, recorded_by=drivers[0].id))
            db.add(HubReceipt(trip_id=pickup_trip.id, hub_id=central.id, crop_id=crops[0].id, kg_driver=20, kg_hub=20, grade_a_kg=18, grade_b_kg=2, recorded_by=users[UserRole.HUB_STAFF][0].id))
            db.add(StockLedger(hub_id=central.id, crop_id=crops[0].id, delta_kg=20, reason=LedgerReason.PICKUP, ref_type="hub_receipt", ref_id=pickup_trip.id, created_by=users[UserRole.HUB_STAFF][0].id))
        active_trip = db.scalar(select(Trip).where(Trip.assigned_by == admin.id, Trip.driver_id == drivers[1].id, Trip.type == TripType.FIRST_MILE, Trip.status == TripStatus.ASSIGNED))
        if active_trip is None:
            active_trip = Trip(type=TripType.FIRST_MILE, status=TripStatus.ASSIGNED, driver_id=drivers[1].id, vehicle_id=vehicles[1].id, origin_hub_id=village_b.id, dest_hub_id=central.id, assigned_by=admin.id, planned_start=datetime.now(timezone.utc) + timedelta(hours=1))
            db.add(active_trip)
            db.flush()
            active_listing = db.scalar(select(FarmerListing).where(FarmerListing.farmer_id == farmers[1].id, FarmerListing.crop_id == crops[1].id, FarmerListing.listing_date == today))
            db.add(TripStop(trip_id=active_trip.id, seq=1, type=StopType.PICKUP, status=StopStatus.PLANNED, farmer_id=farmers[1].id, listing_id=active_listing.id if active_listing else None, location={"lat": 13.4355, "lng": 77.7315}))

        # A pending order and historical delivered order make buyer history immediately useful.
        for buyer_user, order_status in [(buyers[0], OrderStatus.PLACED), (buyers[1], OrderStatus.DELIVERED)]:
            if not db.scalar(select(Order).where(Order.buyer_id == buyer_user.id, Order.delivery_date == today + timedelta(days=1))):
                order = Order(buyer_id=buyer_user.id, delivery_hub_id=city_a.id, delivery_date=today + timedelta(days=1), status=order_status, subtotal=75000, delivery_fee=7500, total=82500, payment_mode=PaymentMode.PREPAID)
                db.add(order)
                db.flush()
                db.add(OrderItem(order_id=order.id, crop_id=crops[0].id, qty_kg=25, confirmed_kg=25, delivered_kg=25 if order_status == OrderStatus.DELIVERED else None, price_per_kg_locked=3000))

        if not db.scalar(select(TransferRequest).where(TransferRequest.requested_by == users[UserRole.ADMIN][0].id, TransferRequest.crop_id == crops[0].id)):
            db.add(TransferRequest(from_hub_id=central.id, to_hub_id=city_a.id, crop_id=crops[0].id, requested_kg=20, status=TransferStatus.REQUESTED, requested_by=users[UserRole.ADMIN][0].id))

        return {f"{role.value}_phone_{i+1}": user.phone for role, records in users.items() for i, user in enumerate(records)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Seed only the dedicated krishilink_demo.db")
    args = parser.parse_args()
    if not args.demo:
        parser.error("pass --demo to seed the isolated demo database")
    for key, value in seed().items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
