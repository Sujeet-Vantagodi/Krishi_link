"""Capture an immutable delivery address for checkout orders."""
from alembic import op
import sqlalchemy as sa

revision = "0005_order_address"
down_revision = "0004_transfer_urgency"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("orders", sa.Column("delivery_address", sa.String(500)))


def downgrade():
    op.drop_column("orders", "delivery_address")
