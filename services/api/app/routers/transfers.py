import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.exceptions import ForbiddenException, NotFoundException
from app.database import get_db
from app.models.enums import TransferStatus, UserRole
from app.models.hub import HubStaff
from app.models.trip import TransferRequest
from app.models.user import User
from app.schemas.transfer import TransferCreate, TransferDispatch, TransferOut, TransferReceive
from app.services import transfer_service

router = APIRouter(prefix="/transfers", tags=["Inter-hub Transfers"])


def _assert_hub_access(db: Session, user: User, hub_id: uuid.UUID) -> None:
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return
    if not db.get(HubStaff, (user.id, hub_id)):
        raise ForbiddenException("Hub staff may only operate transfers for an assigned hub")


@router.get("", response_model=dict)
def list_transfers(status_filter: Optional[TransferStatus] = Query(None, alias="status"), db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HUB_STAFF))):
    items = transfer_service.list_transfers(db, status_filter)
    return {"items": [TransferOut.model_validate(item).model_dump(mode="json") for item in items], "total": len(items)}


@router.post("", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
def create_transfer(payload: TransferCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HUB_STAFF))):
    _assert_hub_access(db, user, payload.from_hub_id)
    return transfer_service.create_transfer(db, user, **payload.model_dump())


@router.post("/{transfer_id}/approve", response_model=TransferOut)
def approve_transfer(transfer_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    return transfer_service.approve_transfer(db, transfer_id, user)


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
