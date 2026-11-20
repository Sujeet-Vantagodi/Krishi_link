"""Add password credentials to the API-owned schema."""

from alembic import op
import sqlalchemy as sa

revision = "0003_password_credentials"
down_revision = "0002_operational_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_credentials",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("contact_email", sa.String(120)),
    )


def downgrade():
    op.drop_table("password_credentials")
