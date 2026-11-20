import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.crop import Crop
from app.models.trip import LocationPing, Trip, TripStop
from app.models.base import utc_now
from datetime import timezone
from math import ceil
from app.models.enums import UserRole, OrderStatus, TripStatus
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderItemResponse,
    OrderTrackingResponse, ConfirmDeliveryRequest
)
from app.core.dependencies import require_roles, get_current_user
from app.core.exceptions import NotFoundException, ForbiddenException, CutoffPassedException
from app.services.order_service import create_buyer_order, confirm_order_delivery

router = APIRouter(prefix="", tags=["Orders"])


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def api_create_order(
    data: OrderCreate,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_roles(UserRole.BUYER)),
    db: Session = Depends(get_db)
):
    key_str = idempotency_key if isinstance(idempotency_key, str) else None
    order = create_buyer_order(
        db=db,
        buyer_id=current_user.id,
        data=data,
        idempotency_key=key_str
    )

    items_resp = []
    for oi in order.items:
        crop = db.query(Crop).filter(Crop.id == oi.crop_id).first()
        items_resp.append(OrderItemResponse(
            id=oi.id,
            crop_id=oi.crop_id,
            crop_name=crop.name_en if crop else None,
            qty_kg=float(oi.qty_kg),
            confirmed_kg=float(oi.confirmed_kg) if oi.confirmed_kg is not None else None,
            delivered_kg=float(oi.delivered_kg) if oi.delivered_kg is not None else None,
            rejected_kg=float(oi.rejected_kg),
            price_per_kg_locked=oi.price_per_kg_locked
        ))

    return OrderResponse(
        id=order.id,
        buyer_id=order.buyer_id,
        delivery_hub_id=order.delivery_hub_id,
        delivery_date=order.delivery_date,
        slot_start=order.slot_start,
        slot_end=order.slot_end,
        status=order.status,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        payment_mode=order.payment_mode,
        created_at=order.created_at,
        items=items_resp,
        delivery_code=getattr(order, "delivery_code", None),
    )


@router.get("/orders", response_model=dict)
def api_list_orders(
    status: Optional[OrderStatus] = Query(None),
    current_user: User = Depends(require_roles(UserRole.BUYER)),
    db: Session = Depends(get_db)
):
    q = db.query(Order).filter(Order.buyer_id == current_user.id)
    if status:
        q = q.filter(Order.status == status)
    orders = q.order_by(Order.created_at.desc()).all()

    items = []
    for o in orders:
        items.append({
            "id": o.id,
            "delivery_date": str(o.delivery_date),
            "status": o.status,
            "total_paise": o.total,
            "item_count": len(o.items),
            "created_at": o.created_at
        })
    return {"items": items, "total": len(items)}


@router.get("/orders/{id}", response_model=OrderResponse)
def api_get_order(
    id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise NotFoundException("Order", id)

    # Row level access: if buyer, must be own order
    if current_user.role == UserRole.BUYER and order.buyer_id != current_user.id:
        raise ForbiddenException("Access to this order is forbidden")

    items_resp = []
    for oi in order.items:
        crop = db.query(Crop).filter(Crop.id == oi.crop_id).first()
        items_resp.append(OrderItemResponse(
            id=oi.id,
            crop_id=oi.crop_id,
            crop_name=crop.name_en if crop else None,
            qty_kg=float(oi.qty_kg),
            confirmed_kg=float(oi.confirmed_kg) if oi.confirmed_kg is not None else None,
            delivered_kg=float(oi.delivered_kg) if oi.delivered_kg is not None else None,
            rejected_kg=float(oi.rejected_kg),
            price_per_kg_locked=oi.price_per_kg_locked
        ))

    return OrderResponse(
        id=order.id,
        buyer_id=order.buyer_id,
        delivery_hub_id=order.delivery_hub_id,
        delivery_date=order.delivery_date,
        slot_start=order.slot_start,
        slot_end=order.slot_end,
        status=order.status,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        payment_mode=order.payment_mode,
        created_at=order.created_at,
        items=items_resp
    )


@router.post("/orders/{id}/cancel")
def api_cancel_order(
    id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.BUYER)),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == id, Order.buyer_id == current_user.id).first()
    if not order:
        raise NotFoundException("Order", id)

    if order.status in [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise ForbiddenException(f"Cannot cancel order in status '{order.status}'")

    order.status = OrderStatus.CANCELLED
    db.commit()
    return {"message": "Order cancelled successfully", "order_id": order.id}


@router.get("/orders/{id}/tracking", response_model=OrderTrackingResponse)
def api_track_order(
    id: uuid.UUID,
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.ADMIN, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise NotFoundException("Order", id)

    if current_user.role == UserRole.BUYER and order.buyer_id != current_user.id:
        raise ForbiddenException("Access to this order tracking is forbidden")

    stop = (db.query(TripStop).join(Trip).filter(
        TripStop.buyer_order_id == id, Trip.status != TripStatus.CANCELLED,
    ).order_by(Trip.created_at.desc()).first())
    driver_info = None
    vehicle_info = None
    eta_mins = None

    if stop and stop.trip:
        trip = stop.trip
        if trip.driver and trip.driver.user:
            driver_info = {
                "name": trip.driver.user.name,
                "phone": trip.driver.user.phone,
                "vehicle_no": trip.vehicle.reg_no if trip.vehicle else None,
            }
        ping = (db.query(LocationPing).filter_by(trip_id=trip.id, driver_id=trip.driver_id)
                .order_by(LocationPing.ts.desc()).first())
        if ping and ping.location and {"lat", "lng"} <= ping.location.keys():
            vehicle_info = {
                "lat": ping.location["lat"],
                "lng": ping.location["lng"],
                "heading": ping.heading,
                "speed_kmh": ping.speed_kmh,
                "updated_at": ping.ts,
            }
        if stop.eta and order.status == OrderStatus.OUT_FOR_DELIVERY:
            eta = stop.eta if stop.eta.tzinfo else stop.eta.replace(tzinfo=timezone.utc)
            remaining = (eta - utc_now()).total_seconds()
            eta_mins = ceil(remaining / 60) if remaining >= 0 else None

    return OrderTrackingResponse(
        order_id=order.id,
        status=order.status,
        trip_id=stop.trip_id if stop else None,
        driver=driver_info,
        vehicle=vehicle_info,
        destination=stop.location if stop and stop.location and {"lat", "lng"} <= stop.location.keys() else None,
        eta_minutes=eta_mins
    )


@router.post("/orders/{id}/confirm-delivery")
def api_confirm_delivery(
    id: uuid.UUID,
    data: ConfirmDeliveryRequest,
    current_user: User = Depends(require_roles(UserRole.BUYER, UserRole.DRIVER)),
    db: Session = Depends(get_db)
):
    order = confirm_order_delivery(db, order_id=id, actor=current_user, otp=data.otp, items=data.items)
    return {"message": "Delivery confirmed with verified quantities", "order_id": order.id, "status": order.status}


@router.post("/calls/masked")
def api_masked_call(
    order_id: Optional[uuid.UUID] = None,
    trip_id: Optional[uuid.UUID] = None,
    target: str = "driver",
    current_user: User = Depends(get_current_user)
):
    raise HTTPException(status_code=501, detail={"error": {"code": "CALL_PROVIDER_UNCONFIGURED", "message": "Masked calling is a development placeholder; no call provider is configured."}})
