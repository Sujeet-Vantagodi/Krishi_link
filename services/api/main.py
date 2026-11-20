"""
KrishiLink Core API Backend (FastAPI)
Conforms to 03_ARCHITECTURE.md, 04_DATABASE_SCHEMA.md, and 05_API_SPEC.md.
Connects directly to the KrishiLink Database and provides REST + OpenAPI docs.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date

# Add workspace root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db, engine
from database.auth_utils import verify_password, hash_password, create_access_token, decode_access_token
from database.models import (
    User, Hub, HubStaff, Vehicle, Driver, Farmer, Buyer, Crop,
    HubStockStatus, StockLedger, Order, OrderItem, Trip, TripStop,
    PublishedPrice, Setting
)

app = FastAPI(
    title="KrishiLink Core API",
    description="Agricultural logistics backend connecting smallholder farmers, village hubs, and city bulk buyers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== AUTH DEPENDENCY ====================

def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

# ==================== REQUEST SCHEMAS ====================

class LoginPayload(BaseModel):
    phone: str
    password: str

class RegisterPayload(BaseModel):
    role: str
    name: str
    phone: str
    password: str = "123456"
    email: Optional[str] = None
    village: Optional[str] = None
    taluk: Optional[str] = None
    land_acres: Optional[float] = 2.0
    min_threshold_kg: Optional[float] = 20.0
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    licence_no: Optional[str] = None
    vehicle_reg: Optional[str] = None
    vehicle_type: Optional[str] = None
    employee_id: Optional[str] = None
    station: Optional[str] = None

class AssignTripPayload(BaseModel):
    driver_id: str
    vehicle_id: str
    hub_id: Optional[str] = "h_kolar"
    type: Optional[str] = "FIRST_MILE"
    stops: List[Dict[str, Any]]

class OtpRequestPayload(BaseModel):
    phone: str

class OtpVerifyPayload(BaseModel):
    phone: str
    otp: str

class StockStatusUpdate(BaseModel):
    status: str # 'OUT', 'LOW', 'SUFFICIENT'

class OrderItemPayload(BaseModel):
    crop_id: str
    qty_kg: float

class CreateOrderPayload(BaseModel):
    delivery_date: str
    slot: str
    payment_mode: str = "PREPAID"
    items: List[OrderItemPayload]
    address: Optional[str] = None
    buyer_id: Optional[str] = None

# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    return {
        "platform": "KrishiLink Agricultural Logistics API",
        "status": "online",
        "version": "1.0.0",
        "documentation": "/docs",
        "api_base": "/api/v1"
    }

@app.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    hub_count = db.query(Hub).count()
    crop_count = db.query(Crop).count()
    return {
        "status": "healthy",
        "database_connected": True,
        "engine": str(engine.url),
        "counts": {
            "users": user_count,
            "hubs": hub_count,
            "crops": crop_count
        }
    }

# ---------- 1. AUTHENTICATION & CREDENTIALS ----------

@app.post("/api/v1/auth/register")
def register_user(payload: RegisterPayload, db: Session = Depends(get_db)):
    clean_phone = payload.phone.replace("+91", "").strip()
    formatted_phone = f"+91{clean_phone}" if not payload.phone.startswith("+91") else payload.phone

    # Check existing user
    existing = db.query(User).filter((User.phone == formatted_phone) | (User.phone.contains(clean_phone))).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this phone number already exists.")

    new_user_id = f"u_{payload.role}_{int(datetime.now().timestamp() * 1000) % 1000000}"
    pwd_hash = hash_password(payload.password)

    new_user = User(
        id=new_user_id,
        phone=formatted_phone,
        role=payload.role,
        name=payload.name,
        email=payload.email or f"{payload.role}_{clean_phone}@krishilink.in",
        password_hash=pwd_hash,
        language="kn" if payload.role == "farmer" else "en",
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # Create role profile
    if payload.role == "farmer":
        farmer = Farmer(
            user_id=new_user_id,
            village=payload.village or "Kolar Rural",
            taluk=payload.taluk or "Kolar",
            district="Kolar",
            latitude=13.1360,
            longitude=78.1290,
            nearest_hub_id="h_kolar",
            land_acres=payload.land_acres or 2.5,
            default_min_kg=payload.min_threshold_kg or 25.0,
            reliability_score=5.0,
            approved=True
        )
        db.add(farmer)
    elif payload.role == "buyer":
        buyer = Buyer(
            user_id=new_user_id,
            business_name=payload.business_name or payload.name,
            business_type=payload.business_type or "Restaurant",
            gstin=payload.gstin,
            address=payload.address or "Bengaluru Central",
            latitude=12.9716,
            longitude=77.5946,
            delivery_hub_id="h_hsr",
            credit_limit=10000000,
            credit_due=0,
            approved=True
        )
        db.add(buyer)
    elif payload.role == "driver":
        vehicle_id = "v_1"
        if payload.vehicle_reg:
            veh = db.query(Vehicle).filter(Vehicle.reg_no == payload.vehicle_reg).first()
            if veh:
                vehicle_id = veh.id
            else:
                vehicle_id = f"v_{int(datetime.now().timestamp()) % 10000}"
                db.add(Vehicle(id=vehicle_id, reg_no=payload.vehicle_reg, type=payload.vehicle_type or "Tata Ace", capacity_kg=1000.0, ownership="rent", active=True))
                db.flush()

        driver = Driver(
            user_id=new_user_id,
            licence_no=payload.licence_no or f"KA-DL-{clean_phone[-6:]}",
            vehicle_id=vehicle_id,
            home_hub_id="h_kolar",
            on_duty=True
        )
        db.add(driver)

    db.commit()

    token = create_access_token(new_user.id, new_user.role, new_user.phone)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "phone": new_user.phone,
            "role": new_user.role,
            "language": new_user.language
        }
    }

@app.post("/api/v1/auth/login")
def login_with_password(payload: LoginPayload, db: Session = Depends(get_db)):
    clean_phone = payload.phone.replace("+91", "").strip()
    user = db.query(User).filter((User.phone == payload.phone) | (User.phone.contains(clean_phone))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone number or password")
    
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone number or password")

    token = create_access_token(user.id, user.role, user.phone)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "language": user.language
        }
    }

@app.post("/api/v1/auth/otp/request")
def request_otp(payload: OtpRequestPayload, db: Session = Depends(get_db)):
    clean_phone = payload.phone.replace("+91", "").strip()
    user = db.query(User).filter(User.phone.contains(clean_phone)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found with this phone")
    
    return {
        "request_id": f"req_{user.id}_{int(datetime.now().timestamp())}",
        "message": f"OTP sent to {user.phone}. Demo default OTP: 123456"
    }

@app.post("/api/v1/auth/otp/verify")
def verify_otp(payload: OtpVerifyPayload, db: Session = Depends(get_db)):
    clean_phone = payload.phone.replace("+91", "").strip()
    user = db.query(User).filter(User.phone.contains(clean_phone)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not registered")
    
    if payload.otp != "123456" and len(payload.otp) != 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code")

    token = create_access_token(user.id, user.role, user.phone)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "role": user.role,
            "language": user.language
        }
    }

@app.get("/api/v1/me")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = None
    if current_user.role == "farmer" and current_user.farmer_profile:
        fp = current_user.farmer_profile
        profile = {
            "village": fp.village,
            "taluk": fp.taluk,
            "district": fp.district,
            "nearest_hub_id": fp.nearest_hub_id,
            "land_acres": fp.land_acres,
            "upi_id": fp.upi_id,
            "reliability_score": fp.reliability_score
        }
    elif current_user.role == "buyer" and current_user.buyer_profile:
        bp = current_user.buyer_profile
        profile = {
            "business_name": bp.business_name,
            "business_type": bp.business_type,
            "gstin": bp.gstin,
            "address": bp.address,
            "delivery_hub_id": bp.delivery_hub_id,
            "credit_limit": bp.credit_limit,
            "credit_due": bp.credit_due
        }
    elif current_user.role == "driver" and current_user.driver_profile:
        dp = current_user.driver_profile
        profile = {
            "licence_no": dp.licence_no,
            "vehicle_id": dp.vehicle_id,
            "home_hub_id": dp.home_hub_id,
            "on_duty": dp.on_duty
        }

    return {
        "id": current_user.id,
        "name": current_user.name,
        "phone": current_user.phone,
        "role": current_user.role,
        "language": current_user.language,
        "profile": profile
    }

# ---------- 2. CROPS & CATALOG ----------

@app.get("/api/v1/crops")
def list_crops(query: Optional[str] = None, category: Optional[str] = None, organic: Optional[bool] = None, db: Session = Depends(get_db)):
    q = db.query(Crop).filter(Crop.active == True)
    if query:
        term = f"%{query.lower()}%"
        q = q.filter((Crop.name_en.ilike(term)) | (Crop.name_kn.ilike(term)))
    if category and category != "all":
        q = q.filter(Crop.category == category)
    if organic is not None:
        q = q.filter(Crop.is_organic == organic)
    
    crops = q.all()
    results = []
    for c in crops:
        pub = db.query(PublishedPrice).filter(PublishedPrice.crop_id == c.id).order_by(PublishedPrice.date.desc()).first()
        price_dict = {
            "low": pub.low if pub else 2000,
            "high": pub.high if pub else 3000,
            "reference": pub.reference if pub else 2500,
            "currency": "INR_PAISE_PER_KG"
        }
        results.append({
            "id": c.id,
            "slug": c.slug,
            "name_en": c.name_en,
            "name_kn": c.name_kn,
            "category": c.category,
            "unit": c.unit,
            "min_order_kg": c.min_order_kg,
            "is_organic": c.is_organic,
            "image_emoji": c.image_emoji,
            "availability": "SUFFICIENT",
            "price": price_dict
        })
    return {"items": results, "total": len(results)}

@app.get("/api/v1/prices/today")
def get_today_prices(db: Session = Depends(get_db)):
    prices = db.query(PublishedPrice).all()
    return [{"crop_id": p.crop_id, "low": p.low, "high": p.high, "reference": p.reference} for p in prices]

# ---------- 3. HUBS & STOCK MATRIX ----------

@app.get("/api/v1/hubs")
def list_hubs(db: Session = Depends(get_db)):
    hubs = db.query(Hub).filter(Hub.active == True).all()
    return [{"id": h.id, "name": h.name, "type": h.type, "latitude": h.latitude, "longitude": h.longitude, "address": h.address, "capacity_kg": h.capacity_kg, "has_cold_room": h.has_cold_room} for h in hubs]

@app.get("/api/v1/hubs/stock-matrix")
def get_stock_matrix(db: Session = Depends(get_db)):
    hubs = db.query(Hub).filter(Hub.active == True).all()
    crops = db.query(Crop).filter(Crop.active == True).all()
    
    matrix = {}
    for h in hubs:
        matrix[h.id] = {}
        for c in crops:
            st = db.query(HubStockStatus).filter(HubStockStatus.hub_id == h.id, HubStockStatus.crop_id == c.id).first()
            status_val = st.status if st else "SUFFICIENT"
            suggested_val = st.suggested if st else status_val
            matrix[h.id][c.id] = {
                "status": status_val,
                "suggested": suggested_val,
                "crop_id": c.id
            }
    return {
        "hubs": [{"id": h.id, "name": h.name, "type": h.type} for h in hubs],
        "crops": [{"id": c.id, "name_en": c.name_en, "name_kn": c.name_kn} for c in crops],
        "matrix": matrix
    }

@app.put("/api/v1/hubs/{hub_id}/stock-status/{crop_id}")
def update_stock_status(hub_id: str, crop_id: str, payload: StockStatusUpdate, db: Session = Depends(get_db)):
    st = db.query(HubStockStatus).filter(HubStockStatus.hub_id == hub_id, HubStockStatus.crop_id == crop_id).first()
    if not st:
        st = HubStockStatus(hub_id=hub_id, crop_id=crop_id, status=payload.status, set_by="u_admin_1")
        db.add(st)
    else:
        st.status = payload.status
        st.set_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "hub_id": hub_id, "crop_id": crop_id, "status": st.status}

# ---------- 4. ORDERS ----------

@app.get("/api/v1/orders")
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    orders = q.order_by(Order.created_at.desc()).all()
    
    results = []
    for o in orders:
        results.append({
            "id": o.id,
            "buyer_id": o.buyer_id,
            "delivery_date": str(o.delivery_date),
            "slot": o.slot,
            "status": o.status,
            "total": o.total,
            "payment_mode": o.payment_mode,
            "items_count": len(o.items)
        })
    return {"items": results, "total": len(results)}

@app.post("/api/v1/orders")
def create_order(payload: CreateOrderPayload, db: Session = Depends(get_db)):
    order_id = f"order_{int(datetime.now().timestamp() * 1000) % 100000}"
    total_paise = 0
    items = []

    for it in payload.items:
        crop = db.query(Crop).filter(Crop.id == it.crop_id).first()
        if not crop:
            raise HTTPException(status_code=404, detail=f"Crop {it.crop_id} not found")
        pub = db.query(PublishedPrice).filter(PublishedPrice.crop_id == crop.id).first()
        unit_price = int(pub.reference if pub else 2500)
        total_paise += unit_price * int(it.qty_kg)
        items.append(OrderItem(
            id=f"oi_{order_id}_{len(items)+1}",
            order_id=order_id,
            crop_id=crop.id,
            qty_kg=it.qty_kg,
            confirmed_kg=it.qty_kg,
            price_per_kg_locked=unit_price,
            note="FULL"
        ))

    new_order = Order(
        id=order_id,
        buyer_id=payload.buyer_id or "u_buyer_1",
        delivery_date=date.today(),
        slot=payload.slot,
        status="CONFIRMED",
        subtotal=total_paise,
        delivery_fee=5000,
        total=total_paise + 5000,
        payment_mode=payload.payment_mode,
        payment_status="SUCCESS",
        delivery_otp="4821",
        address=payload.address or "Udupi Upahar, 14th Main, HSR Layout Sector 4, Bengaluru"
    )
    db.add(new_order)
    db.add_all(items)
    db.commit()

    return {
        "id": new_order.id,
        "status": new_order.status,
        "total": new_order.total,
        "delivery_otp": new_order.delivery_otp,
        "items": len(items)
    }

# ---------- 5. TRIPS & DISPATCH ----------

@app.get("/api/v1/trips")
def list_trips(db: Session = Depends(get_db)):
    trips = db.query(Trip).all()
    results = []
    for t in trips:
        results.append({
            "id": t.id,
            "type": t.type,
            "status": t.status,
            "driver_id": t.driver_id,
            "vehicle_id": t.vehicle_id,
            "total_planned_kg": t.total_planned_kg,
            "total_actual_kg": t.total_actual_kg,
            "stops_count": len(t.stops)
        })
    return {"items": results, "total": len(results)}

@app.post("/api/v1/admin/assign")
def assign_trip_to_driver(payload: AssignTripPayload, db: Session = Depends(get_db)):
    trip_id = f"trip_{int(datetime.now().timestamp() * 1000) % 100000}"
    total_kg = sum(float(s.get("expected_kg") or s.get("actual_kg") or 0.0) for s in payload.stops)

    new_trip = Trip(
        id=trip_id,
        type=payload.type or "FIRST_MILE",
        status="ASSIGNED",
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        origin_hub_id=payload.hub_id or "h_kolar",
        dest_hub_id=payload.hub_id or "h_kolar",
        assigned_by="u_admin_1",
        date=date.today(),
        planned_start=datetime.now(timezone.utc),
        total_planned_kg=total_kg,
        total_actual_kg=0.0
    )
    db.add(new_trip)
    db.flush()

    # Add stops
    for idx, s in enumerate(payload.stops):
        stop_id = f"stop_{trip_id}_{idx+1}"
        loc = s.get("location") or {}
        lat = float(loc.get("lat") or s.get("latitude") or 13.1360)
        lng = float(loc.get("lng") or s.get("longitude") or 78.1290)
        db_stop = TripStop(
            id=stop_id,
            trip_id=trip_id,
            seq=idx + 1,
            type=s.get("type") or "PICKUP",
            status="PLANNED",
            farmer_id=s.get("farmer_id"),
            buyer_order_id=s.get("buyer_order_id") or s.get("order_id"),
            hub_id=s.get("hub_id"),
            name=s.get("name") or f"Stop {idx+1}",
            address=s.get("address") or "Karnataka Agri Hub",
            phone=s.get("phone") or "+919876543200",
            latitude=lat,
            longitude=lng,
            expected_kg=float(s.get("expected_kg") or 0.0),
            actual_kg=0.0,
            eta=s.get("eta") or "06:00"
        )
        db.add(db_stop)

    db.commit()

    return {
        "success": True,
        "trip_id": trip_id,
        "status": "ASSIGNED",
        "driver_id": payload.driver_id,
        "vehicle_id": payload.vehicle_id,
        "total_kg": total_kg,
        "stops_count": len(payload.stops)
    }

@app.get("/api/v1/driver/me/trips")
def get_driver_trips(driver_id: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Trip)
    if driver_id:
        q = q.filter(Trip.driver_id == driver_id)
    trips = q.order_by(Trip.created_at.desc()).all()
    results = []
    for t in trips:
        stops = []
        for s in t.stops:
            stops.append({
                "id": s.id,
                "seq": s.seq,
                "type": s.type,
                "status": s.status,
                "name": s.name,
                "address": s.address,
                "phone": s.phone,
                "expected_kg": s.expected_kg,
                "actual_kg": s.actual_kg,
                "eta": s.eta,
                "location": {"lat": s.latitude, "lng": s.longitude}
            })
        driver_user = db.query(User).filter(User.id == t.driver_id).first()
        veh = db.query(Vehicle).filter(Vehicle.id == t.vehicle_id).first()
        results.append({
            "id": t.id,
            "type": t.type,
            "status": t.status,
            "date": str(t.date),
            "driver_id": t.driver_id,
            "vehicle_id": t.vehicle_id,
            "total_planned_kg": t.total_planned_kg,
            "total_actual_kg": t.total_actual_kg,
            "driver": {"id": driver_user.id, "name": driver_user.name, "phone": driver_user.phone} if driver_user else None,
            "vehicle": {"id": veh.id, "reg_no": veh.reg_no, "type": veh.type} if veh else None,
            "stops": stops
        })
    return {"trips": results}
