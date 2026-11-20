"""Persist the transfer priority shown in the frontend."""

from alembic import op
import sqlalchemy as sa

revision = "0004_transfer_urgency"
down_revision = "0003_password_credentials"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transfer_requests", sa.Column("urgency", sa.String(8), nullable=False, server_default="NORMAL"))


def downgrade():
    op.drop_column("transfer_requests", "urgency")
