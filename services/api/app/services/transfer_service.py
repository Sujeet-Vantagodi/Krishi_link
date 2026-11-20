import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleException, ConflictException, NotFoundException, OutOfStockException
from app.models.crop import Crop
from app.models.enums import LedgerReason, TransferStatus, TripStatus, TripType
from app.models.hub import Hub
from app.models.stock import StockLedger
from app.models.trip import Trip, TransferRequest
from app.models.user import User
from app.services.stock_service import get_hub_physical_stock


def list_transfers(db: Session, status: TransferStatus | None = None,
                   hub_ids: set[uuid.UUID] | None = None) -> list[TransferRequest]:
    query = db.query(TransferRequest)
    if hub_ids is not None:
        query = query.filter(or_(TransferRequest.from_hub_id.in_(hub_ids), TransferRequest.to_hub_id.in_(hub_ids)))
    if status:
        query = query.filter(TransferRequest.status == status)
    return query.order_by(TransferRequest.created_at.desc()).all()


def create_transfer(db: Session, actor: User, *, from_hub_id: uuid.UUID, to_hub_id: uuid.UUID, crop_id: uuid.UUID, requested_kg: float, urgency: str = "NORMAL") -> TransferRequest:
    if from_hub_id == to_hub_id:
        raise BusinessRuleException("Source and destination hubs must differ")
    if not db.get(Hub, from_hub_id):
        raise NotFoundException("Source hub", from_hub_id)
    if not db.get(Hub, to_hub_id):
        raise NotFoundException("Destination hub", to_hub_id)
    if not db.get(Crop, crop_id):
        raise NotFoundException("Crop", crop_id)
    record = TransferRequest(from_hub_id=from_hub_id, to_hub_id=to_hub_id, crop_id=crop_id, requested_kg=requested_kg, status=TransferStatus.REQUESTED, requested_by=actor.id, urgency=urgency)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def approve_transfer(db: Session, transfer_id: uuid.UUID, actor: User) -> TransferRequest:
    transfer = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).with_for_update().first()
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    if transfer.status not in (TransferStatus.REQUESTED, TransferStatus.SUGGESTED):
        raise ConflictException(f"Cannot approve transfer in status {transfer.status.value}")
    transfer.status = TransferStatus.APPROVED
    transfer.approved_by = actor.id
    db.commit()
    db.refresh(transfer)
    return transfer


def reject_transfer(db: Session, transfer_id: uuid.UUID) -> TransferRequest:
    transfer = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).with_for_update().first()
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    if transfer.status != TransferStatus.REQUESTED:
        raise ConflictException(f"Cannot reject transfer in status {transfer.status.value}")
    transfer.status = TransferStatus.REJECTED
    db.commit()
    db.refresh(transfer)
    return transfer


def _verified_transfer_trip(db: Session, transfer: TransferRequest, trip_id: uuid.UUID) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id).with_for_update().first()
    if not trip:
        raise NotFoundException("Trip", trip_id)
    if trip.type != TripType.TRANSFER or trip.origin_hub_id != transfer.from_hub_id or trip.dest_hub_id != transfer.to_hub_id:
        raise BusinessRuleException("Assigned trip must be a TRANSFER trip between the requested hubs")
    if trip.status not in (TripStatus.ASSIGNED, TripStatus.ACKNOWLEDGED, TripStatus.STARTED):
        raise ConflictException("Transfer trip is not dispatchable in its current state")
    return trip


def assign_transfer(db: Session, transfer_id: uuid.UUID, trip_id: uuid.UUID) -> TransferRequest:
    transfer = db.query(TransferRequest).filter_by(id=transfer_id).with_for_update().first()
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    if transfer.status != TransferStatus.APPROVED:
        raise ConflictException("Transfer must be approved before trip assignment")
    transfer.trip_id = _verified_transfer_trip(db, transfer, trip_id).id
    transfer.status = TransferStatus.ASSIGNED
    db.commit()
    db.refresh(transfer)
    return transfer


def dispatch_transfer(db: Session, transfer_id: uuid.UUID, trip_id: uuid.UUID, sent_kg: float, actor: User) -> TransferRequest:
    transfer = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).with_for_update().first()
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    if transfer.status not in (TransferStatus.APPROVED, TransferStatus.ASSIGNED):
        raise ConflictException(f"Transfer must be approved before dispatch (status={transfer.status.value})")
    if transfer.trip_id is not None and transfer.trip_id != trip_id:
        raise ConflictException("Transfer is assigned to a different trip")
    trip = _verified_transfer_trip(db, transfer, trip_id)
    qty = float(sent_kg)
    if qty <= 0 or qty > float(transfer.requested_kg):
        raise BusinessRuleException("sent_kg must be positive and no greater than requested_kg")
    already_loaded = db.scalar(select(func.coalesce(func.sum(TransferRequest.sent_kg), 0)).where(
        TransferRequest.trip_id == trip.id, TransferRequest.status == TransferStatus.IN_TRANSIT,
    ))
    if not trip.vehicle or not trip.vehicle.active or float(already_loaded) + qty > float(trip.vehicle.capacity_kg):
        raise BusinessRuleException("Transfer load exceeds the assigned vehicle's available capacity")

    # Lock both hub rows in stable order so orders and transfers serialize on inventory.
    for hub_id in sorted((transfer.from_hub_id, transfer.to_hub_id), key=str):
        db.execute(select(Hub.id).where(Hub.id == hub_id).with_for_update()).first()
    available = get_hub_physical_stock(db, transfer.from_hub_id, transfer.crop_id)
    if available < qty:
        crop = db.get(Crop, transfer.crop_id)
        raise OutOfStockException(crop.name_en if crop else "crop", available, qty)

    db.add(StockLedger(hub_id=transfer.from_hub_id, crop_id=transfer.crop_id, delta_kg=-qty, reason=LedgerReason.TRANSFER_OUT, ref_type="transfer", ref_id=transfer.id, created_by=actor.id))
    transfer.trip_id = trip.id
    transfer.sent_kg = qty
    transfer.status = TransferStatus.IN_TRANSIT
    db.commit()
    db.refresh(transfer)
    return transfer


def receive_transfer(db: Session, transfer_id: uuid.UUID, received_kg: float, actor: User) -> TransferRequest:
    transfer = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).with_for_update().first()
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    if transfer.status != TransferStatus.IN_TRANSIT:
        raise ConflictException(f"Transfer is not awaiting receipt (status={transfer.status.value})")
    trip = db.query(Trip).filter_by(id=transfer.trip_id).with_for_update().first()
    if not trip or trip.status != TripStatus.AT_HUB or trip.dest_hub_id != transfer.to_hub_id:
        raise ConflictException("The assigned trip must reach the destination hub before receiving stock")
    sent = float(transfer.sent_kg or 0)
    if received_kg <= 0 or received_kg > sent:
        raise BusinessRuleException("received_kg must be positive and cannot exceed the verified sent weight")

    # Destination receipt is the only point that credits destination physical stock.
    db.execute(select(Hub.id).where(Hub.id == transfer.to_hub_id).with_for_update()).first()
    db.add(StockLedger(hub_id=transfer.to_hub_id, crop_id=transfer.crop_id, delta_kg=received_kg, reason=LedgerReason.TRANSFER_IN, ref_type="transfer", ref_id=transfer.id, created_by=actor.id))
    transfer.received_kg = received_kg
    transfer.status = TransferStatus.RECEIVED
    db.commit()
    db.refresh(transfer)
    return transfer
