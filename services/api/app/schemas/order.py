import uuid
from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.enums import OrderStatus, PaymentMode, PaymentStatus


class OrderItemCreate(BaseModel):
    crop_id: uuid.UUID
    qty_kg: float = Field(..., gt=0)


class OrderCreate(BaseModel):
    delivery_date: date
    delivery_hub_id: Optional[uuid.UUID] = None
    slot_start: Optional[time] = None
    slot_end: Optional[time] = None
    payment_mode: PaymentMode = PaymentMode.PREPAID
    items: List[OrderItemCreate] = Field(..., min_length=1)
    delivery_address: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def distinct_crops(self):
        if len({item.crop_id for item in self.items}) != len(self.items):
            raise ValueError("An order may contain each crop only once")
        return self


class CheckoutRequest(BaseModel):
    slot: str = Field(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]-(?:[01][0-9]|2[0-3]):[0-5][0-9]$")
    payment_mode: PaymentMode
    items: list[OrderItemCreate] = Field(min_length=1)
    address: str = Field(min_length=1, max_length=500, pattern=r"\S")

    @model_validator(mode="after")
    def valid_cart(self):
        start, end = self.slot.split("-")
        if start >= end:
            raise ValueError("Delivery slot must end after it starts")
        if len({item.crop_id for item in self.items}) != len(self.items):
            raise ValueError("An order may contain each crop only once")
        return self


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    crop_id: uuid.UUID
    crop_name: Optional[str] = None
    qty_kg: float
    confirmed_kg: Optional[float] = None
    delivered_kg: Optional[float] = None
    rejected_kg: float = 0.0
    price_per_kg_locked: Optional[int] = None  # paise
    note: Optional[str] = None
    substitute_suggestions: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: uuid.UUID
    buyer_id: uuid.UUID
    delivery_hub_id: Optional[uuid.UUID] = None
    delivery_date: date
    slot_start: Optional[time] = None
    slot_end: Optional[time] = None
    status: OrderStatus
    subtotal: Optional[int] = None  # paise
    delivery_fee: Optional[int] = 0  # paise
    total: Optional[int] = None  # paise
    payment_mode: PaymentMode
    delivery_code: Optional[str] = None  # emitted only once by order creation
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class BuyerOrderResponse(OrderResponse):
    address: str
    slot: str
    payment_status: PaymentStatus
    location: dict | None = None


class BuyerOrderHistory(BaseModel):
    items: list[BuyerOrderResponse]


class OrderTrackingResponse(BaseModel):
    order_id: uuid.UUID
    status: OrderStatus
    trip_id: Optional[uuid.UUID] = None
    driver: Optional[dict] = None  # {"name": "...", "vehicle_no": "..."}
    vehicle: Optional[dict] = None  # {"lat": ..., "lng": ..., "heading": ...}
    destination: Optional[dict] = None
    eta_minutes: Optional[int] = None
    route_polyline: Optional[str] = None


class DeliveryItemReport(BaseModel):
    crop_id: uuid.UUID
    received_kg: float = Field(..., ge=0)
    rejected_kg: float = Field(default=0.0, ge=0)
    reason: Optional[str] = None
    photo_url: Optional[str] = None


class DeliveryItemExpected(BaseModel):
    crop_id: uuid.UUID
    crop_name: Optional[str] = None
    qty_kg: float
    confirmed_kg: Optional[float] = None
    delivered_kg: Optional[float] = None
    rejected_kg: float = 0.0


class ConfirmDeliveryRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=8)
    items: List[DeliveryItemReport] = Field(..., min_length=1)
