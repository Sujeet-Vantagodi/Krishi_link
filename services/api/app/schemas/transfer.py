import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransferStatus

TransferUrgency = Literal["LOW", "NORMAL", "HIGH", "CRITICAL"]


class TransferCreate(BaseModel):
    from_hub_id: uuid.UUID
    to_hub_id: uuid.UUID
    crop_id: uuid.UUID
    requested_kg: float = Field(gt=0)
    urgency: TransferUrgency = "NORMAL"


class TransferAssignment(BaseModel):
    trip_id: uuid.UUID


class TransferDispatch(TransferAssignment):
    sent_kg: float = Field(gt=0)


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
    urgency: TransferUrgency
    trip_id: uuid.UUID | None = None
    requested_by: uuid.UUID | None = None
    approved_by: uuid.UUID | None = None
    created_at: datetime
