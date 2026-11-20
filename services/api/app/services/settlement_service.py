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
from app.models.trip import HubReceipt, TripStop


def _paise(amount_rupees: Decimal) -> int:
    return int((amount_rupees * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_settlements(db: Session, settle_date: date) -> list[Settlement]:
    rows = db.execute(
        select(PickupReceipt, FarmerListing, TripStop.trip_id)
        .join(FarmerListing, PickupReceipt.listing_id == FarmerListing.id)
        .join(TripStop, TripStop.id == PickupReceipt.trip_stop_id)
        .where(FarmerListing.listing_date == settle_date)
    ).all()
    loads = {}
    for receipt, listing, trip_id in rows:
        loads.setdefault((trip_id, receipt.crop_id), []).append((receipt, listing))

    grouped: dict[uuid.UUID, tuple[Decimal, Decimal]] = {}
    pending_farmers = set()
    for (trip_id, crop_id), lines in loads.items():
        farmer_ids = {listing.farmer_id for _, listing in lines}
        hub = db.scalar(select(HubReceipt).filter_by(trip_id=trip_id, crop_id=crop_id))
        price = db.scalar(select(PublishedPrice).filter_by(crop_id=crop_id, date=settle_date))
        all_lines = db.scalars(select(PickupReceipt).join(TripStop).where(
            TripStop.trip_id == trip_id, PickupReceipt.crop_id == crop_id,
        )).all()
        if (hub is None or price is None or price.reference <= 0 or len(all_lines) != len(lines)
                or any(not receipt.farmer_confirmed or receipt.grade is None
                       or receipt.crop_id != listing.crop_id for receipt, listing in lines)):
            pending_farmers.update(farmer_ids)
            continue

        accepted = {Grade.A: Decimal(str(hub.grade_a_kg or 0)), Grade.B: Decimal(str(hub.grade_b_kg or 0))}
        pickup_total = sum(Decimal(str(receipt.kg_received)) for receipt in all_lines)
        if (sum(accepted.values()) + Decimal(str(hub.reject_kg or 0)) != Decimal(str(hub.kg_hub))
                or sum(accepted.values()) > pickup_total):
            pending_farmers.update(farmer_ids)
            continue
        quantities = {}
        if len(farmer_ids) == 1:
            quantities[next(iter(farmer_ids))] = sum(accepted.values())
        else:
            if any(sum(Decimal(str(receipt.kg_received)) for receipt in all_lines if receipt.grade == grade)
                   != weight for grade, weight in accepted.items()):
                pending_farmers.update(farmer_ids)
                continue
            for receipt, listing in lines:
                if receipt.grade in accepted:
                    farmer_id = listing.farmer_id
                    quantities[farmer_id] = quantities.get(farmer_id, Decimal("0")) + Decimal(str(receipt.kg_received))
        for farmer_id, weight in quantities.items():
            if weight > 0:
                gross, kg = grouped.get(farmer_id, (Decimal("0"), Decimal("0")))
                grouped[farmer_id] = (gross + weight * Decimal(str(price.reference)), kg + weight)

    results = []
    for farmer_id, (gross_rupees, accepted_kg) in grouped.items():
        if farmer_id in pending_farmers:
            continue
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
