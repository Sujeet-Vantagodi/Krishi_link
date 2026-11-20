import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.models.crop import Crop
from app.models.pricing import PublishedPrice
from app.models.stock import StockLedger
from app.models.hub import Hub
from app.models.enums import StockStatus
from app.schemas.crop import CropResponse, CropCatalogItem, CropCatalogResponse, TodayPricesResponse
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="", tags=["Catalog & Prices"])


@router.get("/crops", response_model=CropCatalogResponse)
def list_crops(
    query: Optional[str] = Query(None, description="Search term for crop name"),
    category: Optional[str] = Query(None, description="leafy, root, fruit_veg, fruit"),
    organic: Optional[bool] = Query(None, description="Filter organic vs regular"),
    db: Session = Depends(get_db)
):
    q = db.query(Crop).filter(Crop.active == True)
    if query:
        pattern = f"%{query}%"
        q = q.filter(or_(Crop.name_en.ilike(pattern), Crop.name_kn.ilike(pattern), Crop.slug.ilike(pattern)))
    if category in {"root", "roots"}:
        q = q.filter(Crop.category.in_(["root", "roots"]))
    elif category:
        q = q.filter(Crop.category == category)
    if organic is not None:
        q = q.filter(Crop.is_organic == organic)

    items = _catalog_items(db, q.order_by(Crop.name_en).all())
    return {"items": items, "total": len(items)}


def _catalog_items(db: Session, crops: list[Crop]) -> list[dict]:
    crop_ids = [crop.id for crop in crops]
    today = date.today()
    prices = db.query(PublishedPrice).filter(
        PublishedPrice.date == today, PublishedPrice.crop_id.in_(crop_ids)
    ).all()
    price_map = {price.crop_id: price for price in prices}
    balances = (
        db.query(StockLedger.crop_id, func.sum(StockLedger.delta_kg).label("kg"))
        .join(Hub, Hub.id == StockLedger.hub_id)
        .filter(Hub.active.is_(True), StockLedger.crop_id.in_(crop_ids))
        .group_by(StockLedger.crop_id, StockLedger.hub_id)
        .subquery()
    )
    best_balances = dict(
        db.query(balances.c.crop_id, func.max(balances.c.kg)).group_by(balances.c.crop_id).all()
    )

    items = []
    for c in crops:
        p = price_map.get(c.id)
        price_info = None if p is None else {
            "low": int(p.low * 100),
            "high": int(p.high * 100),
            "reference": int(p.reference * 100),
            "currency": "INR_PAISE_PER_KG",
            "date": str(today),
        }
        kg = best_balances.get(c.id, 0)
        availability = StockStatus.OUT
        if kg > 0:
            availability = StockStatus.LOW if kg < c.min_order_kg else StockStatus.SUFFICIENT

        items.append({
            "id": c.id,
            "slug": c.slug,
            "name_en": c.name_en,
            "name_kn": c.name_kn,
            "category": c.category,
            "is_organic": c.is_organic,
            "unit": c.unit,
            "shelf_life_hours": c.shelf_life_hours,
            "perishability": c.perishability,
            "min_order_kg": float(c.min_order_kg),
            "default_min_kg": float(c.default_min_kg),
            "icon_url": c.icon_url,
            "active": c.active,
            "price": price_info,
            "availability": availability
        })

    return items


@router.get("/catalog/crops/{id}", response_model=CropCatalogItem)
def get_catalog_crop(id: uuid.UUID, db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == id, Crop.active.is_(True)).first()
    if crop is None:
        raise NotFoundException("Crop", id)
    return _catalog_items(db, [crop])[0]


@router.get("/crops/{id}", response_model=CropResponse)
def get_crop_detail(id: uuid.UUID, db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == id).first()
    if not crop:
        raise NotFoundException("Crop", id)
    return crop


@router.get("/prices/today", response_model=TodayPricesResponse)
def get_today_prices(db: Session = Depends(get_db)):
    today = date.today()
    prices = db.query(PublishedPrice).filter(PublishedPrice.date == today).all()
    return {
        "date": str(today),
        "items": [
            {
                "crop_id": p.crop_id,
                "date": str(today),
                "low": int(p.low * 100),
                "high": int(p.high * 100),
                "reference": int(p.reference * 100),
                "currency": "INR_PAISE_PER_KG",
                "overridden": p.overridden
            }
            for p in prices
        ]
    }
