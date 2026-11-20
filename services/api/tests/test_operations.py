from datetime import date

from sqlalchemy import select

from app.models.enums import Grade, LedgerReason, TransferStatus, TripType, StopType, OrderStatus
from app.models.listing import FarmerListing, PickupReceipt
from app.models.payment import LedgerEntry, Payment, Settlement
from app.models.stock import StockLedger
from app.services import transfer_service
from app.services.settlement_service import approve_settlement, calculate_settlements
from app.services.trip_service import create_and_assign_trip
from app.services.order_service import create_buyer_order, confirm_order_delivery
from app.schemas.order import OrderCreate, OrderItemCreate, DeliveryItemReport
from app.core.exceptions import KrishiLinkException
from app.core.exceptions import ConflictException
from app.core.exceptions import ForbiddenException
from app.routers.hubs import api_hub_weigh_in
from app.routers.auth import api_demo_login, DemoLoginIn
from app.config import settings
from app.models.enums import UserRole
from app.models.user import User
from app.seed_dev import require_demo_database, DEMO_DB
from fastapi import HTTPException
import pytest


def test_transfer_lifecycle_reconciles_both_hub_ledgers(db_session, seed_data):
    f = seed_data
    db_session.add(StockLedger(hub_id=f["village_hub"].id, crop_id=f["tomato"].id, delta_kg=80, reason=LedgerReason.ADJUSTMENT))
    db_session.commit()
    transfer = transfer_service.create_transfer(db_session, f["admin_user"], from_hub_id=f["village_hub"].id, to_hub_id=f["main_hub"].id, crop_id=f["tomato"].id, requested_kg=50)
    transfer = transfer_service.approve_transfer(db_session, transfer.id, f["admin_user"])
    trip = create_and_assign_trip(db_session, admin_user_id=f["admin_user"].id, driver_user_id=f["driver_user"].id, vehicle_id=f["vehicle"].id, trip_type=TripType.TRANSFER, origin_hub_id=f["village_hub"].id, dest_hub_id=f["main_hub"].id, stops_data=[{"type": StopType.HUB.value, "hub_id": str(f["main_hub"].id)}])
    transfer = transfer_service.dispatch_transfer(db_session, transfer.id, trip.id, 48, f["admin_user"])
    assert transfer.status == TransferStatus.IN_TRANSIT
    with pytest.raises(ConflictException):
        transfer_service.dispatch_transfer(db_session, transfer.id, trip.id, 48, f["admin_user"])
    transfer = transfer_service.receive_transfer(db_session, transfer.id, 46, f["hub_staff_user"])
    assert transfer.status == TransferStatus.RECEIVED
    with pytest.raises(ConflictException):
        transfer_service.receive_transfer(db_session, transfer.id, 46, f["hub_staff_user"])
    entries = db_session.scalars(select(StockLedger).where(StockLedger.ref_id == transfer.id)).all()
    assert [(entry.reason, float(entry.delta_kg)) for entry in entries] == [(LedgerReason.TRANSFER_OUT, -48.0), (LedgerReason.TRANSFER_IN, 46.0)]


def test_settlement_is_verified_and_payout_remains_pending(db_session, seed_data):
    f = seed_data
    today = date.today()
    listing = FarmerListing(farmer_id=f["farmer_user"].id, crop_id=f["tomato"].id, listing_date=today, est_kg=20, status="COLLECTED", min_kg_applied=20)
    db_session.add(listing)
    db_session.flush()
    trip = create_and_assign_trip(db_session, admin_user_id=f["admin_user"].id, driver_user_id=f["driver_user"].id, vehicle_id=f["vehicle"].id, trip_type=TripType.FIRST_MILE, stops_data=[{"type": StopType.PICKUP.value, "farmer_id": str(f["farmer_user"].id)}])
    stop = trip.stops[0]
    db_session.add(PickupReceipt(trip_stop_id=stop.id, listing_id=listing.id, crop_id=f["tomato"].id, kg_received=10, grade=Grade.A, farmer_confirmed=True))
    db_session.add(PickupReceipt(trip_stop_id=stop.id, listing_id=listing.id, crop_id=f["tomato"].id, kg_received=5, grade=Grade.REJECT, farmer_confirmed=True))
    db_session.commit()

    settlement, = calculate_settlements(db_session, today)
    assert float(settlement.accepted_kg) == 10
    assert settlement.gross == 26000
    assert settlement.net == 23920
    approve_settlement(db_session, settlement.id, f["admin_user"])
    payment = db_session.scalar(select(Payment).where(Payment.settlement_id == settlement.id))
    assert payment.status.value == "PENDING"
    assert settlement.status == "APPROVED"
    entries = db_session.scalars(select(LedgerEntry).where(LedgerEntry.ref_id == settlement.id)).all()
    assert sum(row.debit for row in entries) == sum(row.credit for row in entries) == settlement.net


def test_delivery_uses_secret_code_and_verified_quantities(db_session, seed_data):
    f = seed_data
    db_session.add(StockLedger(hub_id=f["main_hub"].id, crop_id=f["tomato"].id, delta_kg=40, reason=LedgerReason.ADJUSTMENT))
    db_session.commit()
    order = create_buyer_order(db_session, f["buyer_user"].id, OrderCreate(delivery_date=date.today(), items=[OrderItemCreate(crop_id=f["tomato"].id, qty_kg=10)]))
    code = order.delivery_code
    assert code and len(code) == 4
    order.status = OrderStatus.OUT_FOR_DELIVERY
    db_session.commit()
    report = [DeliveryItemReport(crop_id=f["tomato"].id, received_kg=8, rejected_kg=2)]
    with pytest.raises(KrishiLinkException):
        confirm_order_delivery(db_session, order_id=order.id, actor=f["buyer_user"], otp="0000", items=report)
    with pytest.raises(KrishiLinkException):
        confirm_order_delivery(db_session, order_id=order.id, actor=f["buyer_user"], otp=code, items=[DeliveryItemReport(crop_id=f["tomato"].id, received_kg=11)])
    order = confirm_order_delivery(db_session, order_id=order.id, actor=f["buyer_user"], otp=code, items=report)
    assert order.status == OrderStatus.DELIVERED
    assert float(order.items[0].delivered_kg) == 8
    assert float(order.items[0].rejected_kg) == 2


def test_hub_staff_cannot_reconcile_an_unassigned_hub(db_session, seed_data):
    f = seed_data
    with pytest.raises(ForbiddenException):
        api_hub_weigh_in(id=f["village_hub"].id, crop_id=f["tomato"].id, kg_hub=1, current_user=f["hub_staff_user"], db=db_session)


def test_demo_login_issues_token_only_for_fixed_allowlisted_identity(db_session, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEMO_MODE", False)
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite+pysqlite:///" + DEMO_DB.as_posix())
    admin = User(phone="+919999005001", name="Demo Admin", role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.commit()
    with pytest.raises(HTTPException) as disabled:
        api_demo_login(DemoLoginIn(role=UserRole.ADMIN), db_session)
    assert disabled.value.status_code == 404

    monkeypatch.setattr(settings, "ENABLE_DEMO_MODE", True)
    result = api_demo_login(DemoLoginIn(role=UserRole.ADMIN), db_session)
    assert result["user"]["id"] == str(admin.id)
    assert result["user"]["role"] == "admin"
    assert result["demo_mode"] is True
    assert result["access_token"] and result["access_token"] != "demo-session"


def test_demo_seed_refuses_non_demo_sqlite_database(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "ENABLE_DEMO_MODE", True)
    monkeypatch.setattr(settings, "MOCK_OTP", True)
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite+pysqlite:///:memory:")
    with pytest.raises(SystemExit, match="Refusing demo seed"):
        require_demo_database()
