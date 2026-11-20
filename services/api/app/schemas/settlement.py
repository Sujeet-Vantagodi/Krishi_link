import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.models.payment import Settlement


class SettlementResponse(BaseModel):
    id: uuid.UUID
    farmer_id: uuid.UUID
    farmer_name: str | None
    date: date
    accepted_kg: float
    gross_amount: int
    commission_amount: int
    logistics_share: int
    net_amount: int
    status: Literal["DRAFT", "APPROVED", "PAID"]
    paid_at: datetime | None

    @classmethod
    def from_record(cls, record: Settlement) -> "SettlementResponse":
        return cls(
            id=record.id,
            farmer_id=record.farmer_id,
            farmer_name=record.farmer.user.name,
            date=record.settle_date,
            accepted_kg=record.accepted_kg,
            gross_amount=record.gross,
            commission_amount=record.commission,
            logistics_share=record.logistics_share,
            net_amount=record.net,
            status=record.status,
            paid_at=record.paid_at,
        )


class SettlementsResponse(BaseModel):
    items: list[SettlementResponse]
    total: int
