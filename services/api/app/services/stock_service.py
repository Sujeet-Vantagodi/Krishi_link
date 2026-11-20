import uuid
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.stock import HubStockStatus, HubStockStatusHistory, StockLedger
from app.models.hub import Hub
from app.models.crop import Crop
from app.models.base import utc_now
from app.models.enums import StockStatus, LedgerReason
from app.core.exceptions import NotFoundException


def lock_hub_inventory(db: Session, hub_id: uuid.UUID) -> Hub:
    """Serialize stock-changing transactions per hub on databases with row locks."""
    hub = db.query(Hub).filter(Hub.id == hub_id).with_for_update().first()
    if not hub:
        raise NotFoundException("Hub", hub_id)
    return hub


def get_hub_physical_stock(db: Session, hub_id: uuid.UUID, crop_id: uuid.UUID) -> float:
    """
    Calculates the actual physical stock kg of a crop at a hub
    from the immutable stock_ledger.
    """
    result = db.query(func.coalesce(func.sum(StockLedger.delta_kg), 0.0)).filter(
        StockLedger.hub_id == hub_id,
        StockLedger.crop_id == crop_id
    ).scalar()
    return float(result)


def update_hub_stock_status(
    db: Session,
    hub_id: uuid.UUID,
    crop_id: uuid.UUID,
    status: StockStatus,
    set_by_user_id: Optional[uuid.UUID] = None,
    source: str = "manual"
) -> HubStockStatus:
    hub = db.query(Hub).filter(Hub.id == hub_id).first()
    if not hub:
        raise NotFoundException("Hub", hub_id)
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise NotFoundException("Crop", crop_id)

    record = db.query(HubStockStatus).filter(
        HubStockStatus.hub_id == hub_id,
        HubStockStatus.crop_id == crop_id
    ).first()

    old_status = record.status if record else None

    if not record:
        record = HubStockStatus(
            hub_id=hub_id,
            crop_id=crop_id,
            status=status,
            set_by=set_by_user_id
        )
        db.add(record)
    else:
        record.status = status
        record.set_by = set_by_user_id
        record.set_at = utc_now()

    # Record history audit
    history = HubStockStatusHistory(
        hub_id=hub_id,
        crop_id=crop_id,
        old_status=old_status,
        new_status=status,
        source=source,
        set_by=set_by_user_id
    )
    db.add(history)
    db.commit()
    db.refresh(record)
    return record


def record_ledger_transaction(
    db: Session,
    hub_id: uuid.UUID,
    crop_id: uuid.UUID,
    delta_kg: float,
    reason: LedgerReason,
    created_by: Optional[uuid.UUID] = None,
    ref_type: Optional[str] = None,
    ref_id: Optional[uuid.UUID] = None
) -> StockLedger:
    ledger_entry = StockLedger(
        hub_id=hub_id,
        crop_id=crop_id,
        delta_kg=delta_kg,
        reason=reason,
        ref_type=ref_type,
        ref_id=ref_id,
        created_by=created_by
    )
    db.add(ledger_entry)
    db.flush()
    return ledger_entry


def get_stock_matrix_data(db: Session, hub_ids: set[uuid.UUID] | None = None) -> Dict:
    crops = db.query(Crop).filter(Crop.active == True).order_by(Crop.name_en).all()
    hubs_query = db.query(Hub).filter(Hub.active.is_(True))
    if hub_ids is not None:
        hubs_query = hubs_query.filter(Hub.id.in_(hub_ids))
    hubs = hubs_query.order_by(Hub.name).all()
    visible_hub_ids = [hub.id for hub in hubs]

    status_records = db.query(HubStockStatus).options(joinedload(HubStockStatus.setter)).filter(
        HubStockStatus.hub_id.in_(visible_hub_ids)
    ).all()
    status_map = {(s.hub_id, s.crop_id): s for s in status_records}
    balances = {
        (hub_id, crop_id): kg
        for hub_id, crop_id, kg in db.query(
            StockLedger.hub_id, StockLedger.crop_id, func.sum(StockLedger.delta_kg)
        ).filter(StockLedger.hub_id.in_(visible_hub_ids)).group_by(
            StockLedger.hub_id, StockLedger.crop_id
        ).all()
    }

    hub_rows = []
    for h in hubs:
        cells = []
        for c in crops:
            s_rec = status_map.get((h.id, c.id))
            balance = balances.get((h.id, c.id), 0)
            measured_status = StockStatus.OUT
            if balance > 0:
                measured_status = StockStatus.LOW if balance < c.min_order_kg else StockStatus.SUFFICIENT
            status = s_rec.status if s_rec else measured_status
            suggested = s_rec.suggested if s_rec and s_rec.suggested else measured_status
            set_by_name = s_rec.setter.name if s_rec and s_rec.setter else None
            set_at = s_rec.set_at if s_rec else None

            cells.append({
                "crop_id": c.id,
                "crop_name": c.name_en,
                "status": status,
                "suggested": suggested,
                "exact_kg": balance,
                "set_by": set_by_name,
                "set_at": set_at
            })
        hub_rows.append({
            "id": h.id,
            "name": h.name,
            "type": h.type,
            "cells": cells
        })

    return {
        "crops": [{"id": c.id, "name": c.name_en, "name_kn": c.name_kn} for c in crops],
        "hubs": hub_rows
    }
