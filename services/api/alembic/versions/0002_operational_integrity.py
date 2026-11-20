"""Operational delivery credentials, receipt uniqueness, and native PostGIS points.

Revision ID: 0002_operational_integrity
Revises: 0001_initial_schema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_operational_integrity"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


class GeographyPoint(sa.types.UserDefinedType):
    def get_col_spec(self, **kw):
        return "geography(POINT,4326)"


def upgrade() -> None:
    # 0001 stored EWKT strings. Convert without dropping or rewriting application data.
    for table in ("hubs", "farmers", "buyers", "trip_stops", "location_pings"):
        op.alter_column(
            table,
            "location",
            existing_type=sa.Text(),
            type_=GeographyPoint(),
            postgresql_using="location::geography(POINT,4326)",
        )
    op.add_column("orders", sa.Column("delivery_code_hash", sa.String(length=64), nullable=True))
    op.add_column("trip_stops", sa.Column("listing_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_trip_stops_listing_id_farmer_listings", "trip_stops", "farmer_listings", ["listing_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_trip_stops_listing_id", "trip_stops", ["listing_id"])
    op.create_unique_constraint("uq_hub_receipt_trip_crop", "hub_receipts", ["trip_id", "crop_id"])


def downgrade() -> None:
    op.drop_constraint("uq_hub_receipt_trip_crop", "hub_receipts", type_="unique")
    op.drop_index("ix_trip_stops_listing_id", table_name="trip_stops")
    op.drop_constraint("fk_trip_stops_listing_id_farmer_listings", "trip_stops", type_="foreignkey")
    op.drop_column("trip_stops", "listing_id")
    op.drop_column("orders", "delivery_code_hash")
    for table in ("hubs", "farmers", "buyers", "trip_stops", "location_pings"):
        op.alter_column(
            table,
            "location",
            existing_type=GeographyPoint(),
            type_=sa.Text(),
            postgresql_using="ST_AsEWKT(location)",
        )
