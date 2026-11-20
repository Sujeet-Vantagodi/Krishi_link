"""
Pydantic v2 Schemas
Defines request and response validation models for Authentication, Crops, Orders, Trips, and Users.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# ==================== AUTH SCHEMAS ====================

class LoginRequest(BaseModel):
    phone: str = Field(..., description="Phone number with or without country code")
    password: str = Field(..., description="User password")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class OtpRequest(BaseModel):
    phone: str

class OtpVerify(BaseModel):
    request_id: str
    otp: str

class UserResponse(BaseModel):
    id: str
    phone: str
    role: str
    name: str
    email: Optional[str] = None
    language: str
    is_active: bool

# ==================== CATALOG & CROPS SCHEMAS ====================

class CropPrice(BaseModel):
    low: float # paise
    high: float # paise
    reference: float # paise
    date: str

class CropResponse(BaseModel):
    id: str
    slug: str
    name_en: str
    name_kn: Optional[str] = None
    category: str
    unit: str = "kg"
    min_order_kg: float
    is_organic: bool
    availability: Optional[str] = "SUFFICIENT"
    image_emoji: Optional[str] = None
    price: Optional[CropPrice] = None

# ==================== ORDER SCHEMAS ====================

class OrderItemInput(BaseModel):
    crop_id: str
    qty_kg: float

class CreateOrderRequest(BaseModel):
    delivery_date: str
    slot: str
    payment_mode: str = "PREPAID"
    items: List[OrderItemInput]
    address: Optional[str] = None
    buyer_id: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    buyer_id: str
    delivery_date: date
    slot: Optional[str]
    status: str
    total: int
    items: List[Dict[str, Any]]

# ==================== TRIP & DISPATCH SCHEMAS ====================

class StopReceiptInput(BaseModel):
    crop_id: str
    kg_received: float
    grade: str = "A"
    photo_url: Optional[str] = None
    farmer_confirmed: bool = True
    client_event_id: Optional[str] = None

class LocationPingInput(BaseModel):
    trip_id: str
    ts: datetime
    lat: float
    lng: float
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    accuracy_m: Optional[float] = None
