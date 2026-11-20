"""
KrishiLink Agricultural Logistics Platform - Live Terminal Database Viewer
Usage:
    python database/view_db.py              # Display summary and all tables
    python database/view_db.py users        # View Users & Credentials table
    python database/view_db.py farmers      # View Farmers table
    python database/view_db.py buyers       # View Buyers table
    python database/view_db.py drivers      # View Drivers & Fleet table
    python database/view_db.py trips        # View Dispatched Trips & Stops
    python database/view_db.py orders       # View Live Orders table
    python database/view_db.py hubs         # View Logistics Hubs
    python database/view_db.py --watch      # Live auto-refresh every 3 seconds
"""

import sys
import os
import time
import argparse
from datetime import datetime

# Add root directory to python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.connection import SessionLocal, engine
from database.models import (
    User, Farmer, Buyer, Driver, Vehicle, Hub, Crop, 
    Trip, TripStop, Order, OrderItem, HubStockStatus
)


def format_table(headers, rows, max_col_width=32):
    """Render a clean, aligned ASCII table compatible with all Windows terminals."""
    if not rows:
        col_widths = [len(h) for h in headers]
    else:
        col_widths = []
        for i, h in enumerate(headers):
            max_len = len(h)
            for row in rows:
                val_str = str(row[i] if i < len(row) and row[i] is not None else "")
                if len(val_str) > max_col_width:
                    val_str = val_str[:max_col_width-3] + "..."
                if len(val_str) > max_len:
                    max_len = len(val_str)
            col_widths.append(max(max_len, len(h)))

    # Separator lines
    sep_line = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "|" + "|".join(f" {headers[i].ljust(col_widths[i])} " for i in range(len(headers))) + "|"

    output = [sep_line, header_line, sep_line]
    if not rows:
        empty_msg = "No records found"
        total_w = sum(col_widths) + 3 * len(col_widths) - 1
        output.append(f"| {empty_msg.center(total_w - 2)} |")
    else:
        for row in rows:
            formatted_vals = []
            for i in range(len(headers)):
                val_str = str(row[i] if i < len(row) and row[i] is not None else "")
                if len(val_str) > max_col_width:
                    val_str = val_str[:max_col_width-3] + "..."
                formatted_vals.append(f" {val_str.ljust(col_widths[i])} ")
            output.append("|" + "|".join(formatted_vals) + "|")
    output.append(sep_line)
    return "\n".join(output)


def view_users(db):
    users = db.query(User).order_by(User.created_at.desc()).all()
    headers = ["USER ID", "FULL NAME", "ROLE", "PHONE", "PASSWORD HASH (BCRYPT)", "LANG", "ACTIVE", "CREATED AT"]
    rows = []
    for u in users:
        # Show first 15 chars of bcrypt hash for clean presentation
        hash_preview = (u.password_hash[:18] + "...") if u.password_hash else "None"
        created_str = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A"
        rows.append([
            u.id,
            u.name or "N/A",
            u.role.upper(),
            u.phone,
            hash_preview,
            u.language or "en",
            "YES" if u.is_active else "NO",
            created_str
        ])
    print("\n" + "="*90)
    print(f" [TABLE: USERS & AUTHENTICATION CREDENTIALS] - {len(users)} registered accounts")
    print("="*90)
    print(format_table(headers, rows, max_col_width=25))


def view_farmers(db):
    farmers = db.query(Farmer).all()
    headers = ["USER ID", "FARMER NAME", "PHONE", "VILLAGE", "TALUK", "ACRES", "MIN KG", "NEAREST HUB", "RATING"]
    rows = []
    for f in farmers:
        user = db.query(User).filter(User.id == f.user_id).first()
        rows.append([
            f.user_id,
            user.name if user else "N/A",
            user.phone if user else "N/A",
            f.village or "N/A",
            f.taluk or "N/A",
            f"{float(f.land_acres):.1f}" if f.land_acres else "0.0",
            f"{float(f.default_min_kg):.0f} kg" if f.default_min_kg else "20 kg",
            f.nearest_hub_id or "N/A",
            f"{float(f.reliability_score):.1f} ★" if f.reliability_score else "5.0 ★"
        ])
    print("\n" + "="*90)
    print(f" [TABLE: FARMERS DIRECTORY & AGGREGATION] - {len(farmers)} farmers registered")
    print("="*90)
    print(format_table(headers, rows, max_col_width=20))


def view_buyers(db):
    buyers = db.query(Buyer).all()
    headers = ["USER ID", "BUSINESS NAME", "TYPE", "DELIVERY HUB", "CREDIT LIMIT", "ADDRESS", "APPROVED"]
    rows = []
    for b in buyers:
        limit_inr = f"₹{b.credit_limit // 100:,}" if b.credit_limit else "₹0"
        rows.append([
            b.user_id,
            b.business_name or "N/A",
            b.business_type or "Restaurant",
            b.delivery_hub_id or "h_hsr",
            limit_inr,
            b.address or "Bengaluru",
            "YES" if b.approved else "NO"
        ])
    print("\n" + "="*90)
    print(f" [TABLE: BUYERS DIRECTORY & INSTITUTIONAL ACCOUNTS] - {len(buyers)} buyers registered")
    print("="*90)
    print(format_table(headers, rows, max_col_width=25))


def view_drivers(db):
    drivers = db.query(Driver).all()
    headers = ["USER ID", "DRIVER NAME", "PHONE", "LICENCE NO", "VEHICLE ID", "BASE HUB", "ON DUTY"]
    rows = []
    for d in drivers:
        user = db.query(User).filter(User.id == d.user_id).first()
        rows.append([
            d.user_id,
            user.name if user else "N/A",
            user.phone if user else "N/A",
            d.licence_no or "N/A",
            d.vehicle_id or "v_1",
            d.home_hub_id or "h_kolar",
            "YES (ACTIVE)" if d.on_duty else "OFF DUTY"
        ])
    print("\n" + "="*90)
    print(f" [TABLE: DRIVERS & FLEET PILOTS] - {len(drivers)} drivers registered")
    print("="*90)
    print(format_table(headers, rows, max_col_width=22))


def view_trips(db):
    trips = db.query(Trip).order_by(Trip.created_at.desc()).limit(20).all()
    headers = ["TRIP ID", "TYPE", "DRIVER ID", "VEHICLE", "STATUS", "PLANNED KG", "STOPS", "CREATED AT"]
    rows = []
    for t in trips:
        stop_count = db.query(TripStop).filter(TripStop.trip_id == t.id).count()
        planned_kg = f"{float(t.total_planned_kg):.0f} kg" if t.total_planned_kg else "0 kg"
        created_str = t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "N/A"
        rows.append([
            t.id,
            t.type,
            t.driver_id or "Unassigned",
            t.vehicle_id or "v_1",
            t.status,
            planned_kg,
            f"{stop_count} stops",
            created_str
        ])
    print("\n" + "="*90)
    print(f" [TABLE: DISPATCHED TRIPS & LOGISTICS RUNS] - {len(trips)} recent trips")
    print("="*90)
    print(format_table(headers, rows, max_col_width=20))


def view_orders(db):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(20).all()
    headers = ["ORDER ID", "BUYER ID", "DELIVERY DATE", "SLOT", "STATUS", "TOTAL (INR)", "ITEMS", "OTP"]
    rows = []
    for o in orders:
        item_count = db.query(OrderItem).filter(OrderItem.order_id == o.id).count()
        total_rs = f"₹{o.total / 100:.2f}" if o.total else "₹0.00"
        rows.append([
            o.id,
            o.buyer_id,
            str(o.delivery_date),
            o.slot or "SLOT_MORNING_5_7",
            o.status,
            total_rs,
            f"{item_count} items",
            o.delivery_otp or "----"
        ])
    print("\n" + "="*90)
    print(f" [TABLE: BUYER ORDERS & FULFILLMENT] - {len(orders)} recent orders")
    print("="*90)
    print(format_table(headers, rows, max_col_width=20))


def view_hubs(db):
    hubs = db.query(Hub).all()
    headers = ["HUB ID", "HUB NAME", "TYPE", "TALUK", "CAPACITY", "STATUS"]
    rows = []
    for h in hubs:
        rows.append([
            h.id,
            h.name,
            h.type,
            h.taluk or "Bengaluru / Kolar",
            f"{float(h.capacity_kg) / 1000:.1f} MT" if h.capacity_kg else "10.0 MT",
            "OPERATIONAL" if h.active else "INACTIVE"
        ])
    print("\n" + "="*90)
    print(f" [TABLE: LOGISTICS HUBS NETWORK] - {len(hubs)} hubs configured")
    print("="*90)
    print(format_table(headers, rows, max_col_width=25))


def print_summary_card(db):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_count = db.query(User).count()
    farmer_count = db.query(Farmer).count()
    buyer_count = db.query(Buyer).count()
    driver_count = db.query(Driver).count()
    hub_count = db.query(Hub).count()
    trip_count = db.query(Trip).count()
    order_count = db.query(Order).count()

    print("\n" + "#"*90)
    print("  KRISHILINK AGRI-LOGISTICS PLATFORM - LIVE TERMINAL DATABASE VIEWER")
    print(f"  Connected Engine: {engine.url}")
    print(f"  Live Database Snapshot at: {now_str}")
    print("#"*90)
    print(f"  > Total Users:    {user_count:<6} | Farmers: {farmer_count:<5} | Buyers: {buyer_count:<5} | Drivers: {driver_count}")
    print(f"  > Network Hubs:   {hub_count:<6} | Dispatched Trips: {trip_count:<5} | Orders Placed: {order_count}")
    print("#"*90)


def display_all(db):
    print_summary_card(db)
    view_users(db)
    view_farmers(db)
    view_buyers(db)
    view_drivers(db)
    view_trips(db)
    view_orders(db)
    view_hubs(db)


def main():
    parser = argparse.ArgumentParser(description="KrishiLink Live Terminal Database Viewer")
    parser.add_argument("table", nargs="?", default="all", help="Target table: users, farmers, buyers, drivers, trips, orders, hubs, all")
    parser.add_argument("--watch", action="store_true", help="Auto-refresh terminal every 3 seconds")
    parser.add_argument("--interval", type=int, default=3, help="Watch refresh interval in seconds")
    args = parser.parse_args()

    table_map = {
        "users": view_users,
        "farmers": view_farmers,
        "buyers": view_buyers,
        "drivers": view_drivers,
        "trips": view_trips,
        "orders": view_orders,
        "hubs": view_hubs,
    }

    try:
        while True:
            db = SessionLocal()
            try:
                if args.watch:
                    os.system("cls" if os.name == "nt" else "clear")

                target = args.table.lower()
                if target in table_map:
                    print_summary_card(db)
                    table_map[target](db)
                else:
                    display_all(db)

                if not args.watch:
                    break

                print(f"\n[Watch Mode Active] Refreshing in {args.interval}s... Press Ctrl+C to stop.")
                time.sleep(args.interval)
            finally:
                db.close()
    except KeyboardInterrupt:
        print("\nViewer stopped.")


if __name__ == "__main__":
    main()
