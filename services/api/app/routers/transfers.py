import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.exceptions import ForbiddenException, NotFoundException
from app.database import get_db
from app.models.enums import TransferStatus, TripStatus, TripType, UserRole
from app.models.hub import HubStaff
from app.models.trip import TransferRequest, Trip
from app.models.user import User
from app.schemas.transfer import TransferAssignment, TransferCreate, TransferDispatch, TransferOut, TransferReceive
from app.services import transfer_service

router = APIRouter(prefix="/transfers", tags=["Inter-hub Transfers"])


def _assert_hub_access(db: Session, user: User, hub_id: uuid.UUID) -> None:
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return
    if not db.get(HubStaff, (user.id, hub_id)):
        raise ForbiddenException("Hub staff may only operate transfers for an assigned hub")


@router.get("", response_model=dict)
def list_transfers(status_filter: Optional[TransferStatus] = Query(None, alias="status"), db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HUB_STAFF))):
    hub_ids = None
    if user.role == UserRole.HUB_STAFF:
        hub_ids = {hub_id for (hub_id,) in db.query(HubStaff.hub_id).filter_by(user_id=user.id)}
    items = transfer_service.list_transfers(db, status_filter, hub_ids)
    return {"items": [TransferOut.model_validate(item).model_dump(mode="json") for item in items], "total": len(items)}


@router.post("", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HUB_STAFF))):
    _assert_hub_access(db, user, payload.from_hub_id)
    return transfer_service.create_transfer(db, user, **payload.model_dump())


@router.post("/{transfer_id}/approve", response_model=TransferOut)
def approve_transfer(transfer_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    return transfer_service.approve_transfer(db, transfer_id, user)


@router.post("/{transfer_id}/reject", response_model=TransferOut)
def reject_transfer(transfer_id: uuid.UUID, db: Session = Depends(get_db),
                    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    return transfer_service.reject_transfer(db, transfer_id)


@router.get("/{transfer_id}/eligible-trips")
def eligible_transfer_trips(transfer_id: uuid.UUID, db: Session = Depends(get_db),
                            _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    transfer = db.get(TransferRequest, transfer_id)
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    trips = db.query(Trip).filter(
        Trip.type == TripType.TRANSFER, Trip.origin_hub_id == transfer.from_hub_id,
        Trip.dest_hub_id == transfer.to_hub_id,
        Trip.status.in_([TripStatus.ASSIGNED, TripStatus.ACKNOWLEDGED, TripStatus.STARTED]),
    ).all()
    return {"items": [{"id": trip.id, "driver": trip.driver.user.name,
                       "vehicle": trip.vehicle.reg_no} for trip in trips if trip.driver and trip.vehicle and trip.vehicle.active]}


@router.post("/{transfer_id}/assign", response_model=TransferOut)
def assign_transfer(transfer_id: uuid.UUID, payload: TransferAssignment, db: Session = Depends(get_db),
                    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    return transfer_service.assign_transfer(db, transfer_id, payload.trip_id)


@router.post("/{transfer_id}/dispatch", response_model=TransferOut)
def dispatch_transfer(transfer_id: uuid.UUID, payload: TransferDispatch, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    return transfer_service.dispatch_transfer(db, transfer_id, payload.trip_id, payload.sent_kg, user)


@router.post("/{transfer_id}/receive", response_model=TransferOut)
def receive_transfer(transfer_id: uuid.UUID, payload: TransferReceive, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HUB_STAFF))):
    transfer = db.query(TransferRequest).filter(TransferRequest.id == transfer_id).first()
    if not transfer:
        raise NotFoundException("Transfer", transfer_id)
    _assert_hub_access(db, user, transfer.to_hub_id)
    return transfer_service.receive_transfer(db, transfer_id, payload.received_kg, user)
