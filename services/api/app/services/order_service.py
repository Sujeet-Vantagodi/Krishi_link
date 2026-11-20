import uuid
import hashlib
import hmac
import secrets
from datetime import date, datetime, time, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.config import settings
from app.models.order import Order, OrderItem
from app.models.user import Buyer
from app.models.crop import Crop
from app.models.hub import Hub
from app.models.pricing import PublishedPrice
from app.models.stock import StockLedger
from app.models.payment import Payment
from app.models.enums import OrderStatus, PaymentDirection, PaymentMode, PaymentStatus, LedgerReason, StopStatus, UserRole
from app.models.trip import Trip, TripStop
from app.models.user import User
from app.schemas.order import OrderCreate, DeliveryItemReport
from app.services.stock_service import get_hub_physical_stock, lock_hub_inventory
from app.core.exceptions import NotFoundException, OutOfStockException, CutoffPassedException, KrishiLinkException, ForbiddenException, BusinessRuleException, ConflictException


def get_locked_price_paise(db: Session, crop_id: uuid.UUID, target_date: date) -> int:
    """
    Returns locked price in paise (integer) for an item.
    Rules: min(forecast p90, hub reference price). If published price exists, use reference.
    Fallback: baseline 2500 paise (₹25.00/kg).
    """
    published = db.query(PublishedPrice).filter(
        PublishedPrice.crop_id == crop_id,
        PublishedPrice.date == target_date
    ).first()

    if published and published.reference > 0:
        return int(round(published.reference * 100))
    return 2500  # Default ₹25.00/kg in paise


def create_buyer_order(
    db: Session,
    buyer_id: uuid.UUID,
    data: OrderCreate,
    idempotency_key: Optional[str] = None,
    *,
    checkout_quote_date: date | None = None,
) -> Order:
    # 1. Idempotency check
    if idempotency_key:
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).with_for_update().first()
        if existing:
            if existing.buyer_id != buyer_id:
                raise ConflictException("Idempotency key is not available")
            return existing

    buyer = db.query(Buyer).filter(Buyer.user_id == buyer_id).first()
    if not buyer:
        raise NotFoundException("Buyer profile", buyer_id)

    delivery_hub_id = data.delivery_hub_id or buyer.delivery_hub_id
    if delivery_hub_id:
        hub = db.query(Hub).filter(Hub.id == delivery_hub_id).first()
        if not hub:
            raise NotFoundException("Delivery Hub", delivery_hub_id)

    today = date.today()
    is_same_day = data.delivery_date == today

    # 2. Cutoff validation for next-day orders
    if data.delivery_date > today:
        now_utc = datetime.now(timezone.utc)
        cutoff_dt = datetime.combine(
            data.delivery_date - timedelta(days=1),
            time(settings.ORDER_CUTOFF_HOUR_IST),
            tzinfo=timezone(timedelta(hours=5, minutes=30)),
        )
        if now_utc >= cutoff_dt:
            raise CutoffPassedException(
                cutoff_time=f"D-1 {settings.ORDER_CUTOFF_HOUR_IST}:00 IST",
                action="placing next-day orders"
            )

    order_id = uuid.uuid4()
    total_qty = 0.0
    subtotal_paise = 0
    order_items: List[OrderItem] = []

    # 3. Item processing & atomic physical stock verification
    for item_data in data.items:
        crop = db.query(Crop).filter(Crop.id == item_data.crop_id, Crop.active == True).first()
        if not crop:
            raise NotFoundException("Crop", item_data.crop_id)

        if item_data.qty_kg < crop.min_order_kg:
            raise KrishiLinkException(
                status_code=400,
                code="MIN_ORDER_QTY_NOT_MET",
                message=f"Minimum order for {crop.name_en} is {crop.min_order_kg} kg (requested: {item_data.qty_kg} kg)",
                details={"crop": crop.name_en, "min_order_kg": crop.min_order_kg}
            )

        # For same-day orders, verify actual physical stock in the serving hub
        if is_same_day:
            if not delivery_hub_id:
                raise KrishiLinkException(
                    status_code=400,
                    code="HUB_REQUIRED",
                    message="Delivery hub must be specified for same-day delivery stock checks"
                )
            lock_hub_inventory(db, delivery_hub_id)
            physical_stock = get_hub_physical_stock(db, delivery_hub_id, crop.id)
            if physical_stock < item_data.qty_kg:
                raise OutOfStockException(
                    crop_name=crop.name_en,
                    available_kg=physical_stock,
                    requested_kg=item_data.qty_kg
                )

        if checkout_quote_date is None:
            price_locked = get_locked_price_paise(db, crop.id, data.delivery_date)
        else:
            published = db.query(PublishedPrice).filter_by(crop_id=crop.id, date=checkout_quote_date).first()
            if not published or published.reference <= 0:
                raise ConflictException(f"No published price is available for {crop.name_en}")
            price_locked = int(round(published.reference * 100))
        item_subtotal = int(round(price_locked * item_data.qty_kg))
        subtotal_paise += item_subtotal
        total_qty += item_data.qty_kg

        order_item = OrderItem(
            order_id=order_id,
            crop_id=crop.id,
            qty_kg=item_data.qty_kg,
            confirmed_kg=0 if checkout_quote_date is not None and not is_same_day else item_data.qty_kg,
            price_per_kg_locked=price_locked
        )
        order_items.append(order_item)

    # Delivery fee calculation (e.g. ₹1.5/kg in paise -> 150 paise/kg)
    delivery_fee_paise = int(round(total_qty * 150))
    total_paise = subtotal_paise + delivery_fee_paise

    initial_status = OrderStatus.CONFIRMED if is_same_day else OrderStatus.PLACED

    order = Order(
        id=order_id,
        buyer_id=buyer_id,
        delivery_hub_id=delivery_hub_id,
        delivery_date=data.delivery_date,
        slot_start=data.slot_start,
        slot_end=data.slot_end,
        status=initial_status,
        subtotal=subtotal_paise,
        delivery_fee=delivery_fee_paise,
        total=total_paise,
        payment_mode=data.payment_mode,
        delivery_address=data.delivery_address,
        idempotency_key=idempotency_key
    )
    delivery_code = _new_delivery_code()
    order.delivery_code_hash = _delivery_code_hash(delivery_code)
    order.delivery_code = delivery_code

    db.add(order)
    if checkout_quote_date is not None:
        db.add(Payment(party_id=buyer_id, direction=PaymentDirection.IN, amount=total_paise,
                       status=PaymentStatus.PENDING, order_id=order_id))
    for oi in order_items:
        db.add(oi)

    # For same-day orders, immediately record the stock deduction in the ledger
    if is_same_day and delivery_hub_id:
        for item_data in data.items:
            ledger_entry = StockLedger(
                hub_id=delivery_hub_id,
                crop_id=item_data.crop_id,
                delta_kg=-item_data.qty_kg,
                reason=LedgerReason.SALE,
                ref_type="order",
                ref_id=order_id
            )
            db.add(ledger_entry)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key:
            existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
            if existing:
                if existing.buyer_id != buyer_id:
                    raise ConflictException("Idempotency key is not available")
                return existing
        raise
    db.refresh(order)
    return order


def _new_delivery_code() -> str:
    return f"{secrets.randbelow(10_000):04d}"


def _delivery_code_hash(code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256).hexdigest()


def confirm_order_delivery(
    db: Session,
    *,
    order_id: uuid.UUID,
    actor: User,
    otp: str,
    items: list[DeliveryItemReport],
    trip_stop: TripStop | None = None,
) -> Order:
    order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise NotFoundException("Order", order_id)
    if actor.role == UserRole.BUYER and order.buyer_id != actor.id:
        raise ForbiddenException("Buyer may only confirm their own delivery")
    if actor.role == UserRole.DRIVER:
        trip = db.query(Trip).filter(Trip.id == trip_stop.trip_id).first() if trip_stop is not None else None
        if trip_stop is None or trip_stop.buyer_order_id != order.id or trip_stop.type.value != "DELIVERY" or not trip or trip.driver_id != actor.id:
            raise ForbiddenException("Driver is not assigned to this delivery")
    elif order.status != OrderStatus.OUT_FOR_DELIVERY:
        raise ConflictException("Delivery confirmation is only available once the order is out for delivery")
    if not order.delivery_code_hash or not hmac.compare_digest(order.delivery_code_hash, _delivery_code_hash(otp)):
        raise BusinessRuleException("Delivery verification code is invalid or unavailable")
    if not items:
        raise BusinessRuleException("Verified delivered quantities are required")

    expected = {item.crop_id: item for item in order.items}
    reported = {item.crop_id: item for item in items}
    if len(reported) != len(items) or set(reported) != set(expected):
        raise BusinessRuleException("Report one delivered quantity for every ordered crop, without duplicates")
    for crop_id, line in reported.items():
        ordered_line = expected[crop_id]
        delivered = float(line.received_kg)
        rejected = float(line.rejected_kg)
        maximum = float(ordered_line.confirmed_kg if ordered_line.confirmed_kg is not None else ordered_line.qty_kg)
        if delivered + rejected > maximum + 1e-6:
            raise BusinessRuleException(f"Delivered and rejected quantity exceeds the confirmed quantity for crop {crop_id}")
        if order.status == OrderStatus.DELIVERED and (float(ordered_line.delivered_kg or 0) != delivered or float(ordered_line.rejected_kg or 0) != rejected):
            raise ConflictException("Order was already confirmed with different quantities")

    if order.status != OrderStatus.DELIVERED:
        if order.status not in (OrderStatus.ASSIGNED, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.CONFIRMED, OrderStatus.PLACED):
            raise ConflictException(f"Order cannot be delivered from status {order.status.value}")
        for crop_id, line in reported.items():
            order_line = expected[crop_id]
            order_line.delivered_kg = line.received_kg
            order_line.rejected_kg = line.rejected_kg
            order_line.reject_reason = line.reason
        order.status = OrderStatus.DELIVERED
        if trip_stop is not None:
            if trip_stop.status not in (StopStatus.ARRIVED, StopStatus.IN_PROGRESS, StopStatus.COMPLETED):
                raise ConflictException("Delivery stop must be arrived before confirmation")
            trip_stop.status = StopStatus.COMPLETED
            trip_stop.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order
