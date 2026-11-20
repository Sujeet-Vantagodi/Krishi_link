"""Settlement calculations from verified farmer pickup receipts."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import Grade, PaymentDirection, PaymentStatus
from app.models.listing import FarmerListing, PickupReceipt
from app.models.payment import LedgerEntry, Payment, Settlement
from app.models.pricing import PublishedPrice
from app.models.user import Farmer, User


def _paise(amount_rupees: Decimal) -> int:
    return int((amount_rupees * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_settlements(db: Session, settle_date: date) -> list[Settlement]:
    rows = db.execute(
        select(PickupReceipt, FarmerListing, PublishedPrice)
        .join(FarmerListing, PickupReceipt.listing_id == FarmerListing.id)
        .join(PublishedPrice, (PublishedPrice.crop_id == PickupReceipt.crop_id) & (PublishedPrice.date == FarmerListing.listing_date))
        .where(FarmerListing.listing_date == settle_date, PickupReceipt.farmer_confirmed.is_(True), PickupReceipt.grade.in_([Grade.A, Grade.B]))
    ).all()
    grouped: dict[uuid.UUID, tuple[Decimal, Decimal]] = {}
    for receipt, listing, price in rows:
        gross, kg = grouped.get(listing.farmer_id, (Decimal("0"), Decimal("0")))
        grouped[listing.farmer_id] = (gross + Decimal(str(receipt.kg_received)) * Decimal(str(price.reference)), kg + Decimal(str(receipt.kg_received)))

    results = []
    for farmer_id, (gross_rupees, accepted_kg) in grouped.items():
        gross = _paise(gross_rupees)
        commission = int((Decimal(gross) * Decimal("0.05")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        logistics = int((Decimal(gross) * Decimal("0.03")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        settlement = db.scalar(select(Settlement).where(Settlement.farmer_id == farmer_id, Settlement.settle_date == settle_date))
        if settlement is None:
            settlement = Settlement(farmer_id=farmer_id, settle_date=settle_date, accepted_kg=accepted_kg, gross=gross, commission=commission, logistics_share=logistics, net=gross-commission-logistics, status="DRAFT")
            db.add(settlement)
        elif settlement.status == "DRAFT":
            settlement.accepted_kg, settlement.gross, settlement.commission, settlement.logistics_share, settlement.net = accepted_kg, gross, commission, logistics, gross-commission-logistics
        results.append(settlement)
    db.commit()
    for settlement in results:
        db.refresh(settlement)
    return results


def approve_settlement(db: Session, settlement_id: uuid.UUID, actor: User) -> Settlement:
    settlement = db.scalar(select(Settlement).where(Settlement.id == settlement_id).with_for_update())
    if settlement is None:
        raise NotFoundException("Settlement", settlement_id)
    if settlement.status != "DRAFT":
        raise ConflictException(f"Only DRAFT settlements can be approved (status={settlement.status})")
    settlement.status = "APPROVED"
    settlement.approved_by = actor.id
    # This records a payable and a payout intent. External payout stays PENDING until a verified provider callback.
    txn_id = uuid.uuid4()
    db.add_all([
        LedgerEntry(txn_id=txn_id, account="settlement_expense", party_id=None, debit=settlement.net, ref_type="settlement", ref_id=settlement.id),
        LedgerEntry(txn_id=txn_id, account="farmer_payable", party_id=settlement.farmer_id, credit=settlement.net, ref_type="settlement", ref_id=settlement.id),
        Payment(party_id=settlement.farmer_id, direction=PaymentDirection.OUT, amount=settlement.net, status=PaymentStatus.PENDING, settlement_id=settlement.id),
    ])
    db.commit()
    db.refresh(settlement)
    return settlement
