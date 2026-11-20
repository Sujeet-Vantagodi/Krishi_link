import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransferStatus


class TransferCreate(BaseModel):
    from_hub_id: uuid.UUID
    to_hub_id: uuid.UUID
    crop_id: uuid.UUID
    requested_kg: float = Field(gt=0)


class TransferDispatch(BaseModel):
    trip_id: uuid.UUID
    sent_kg: float | None = Field(default=None, gt=0)


class TransferReceive(BaseModel):
    received_kg: float = Field(gt=0)


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_hub_id: uuid.UUID
    to_hub_id: uuid.UUID
    crop_id: uuid.UUID
    requested_kg: float
    sent_kg: float | None = None
    received_kg: float | None = None
    status: TransferStatus
    trip_id: uuid.UUID | None = None
    requested_by: uuid.UUID | None = None
    approved_by: uuid.UUID | None = None
    created_at: datetime
