"""Create transport_requests table.

Revision ID: 057
Revises: 036
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa

revision = "057"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transport_requests",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("requester_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("animal_id", sa.Uuid(), sa.ForeignKey("animals.id"), nullable=True),
        sa.Column("pickup_location", sa.String(500), nullable=False),
        sa.Column("destination", sa.String(500), nullable=False),
        sa.Column("urgency", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("preferred_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("claimed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_transport_requests_status", "transport_requests", ["status"])
    op.create_index("ix_transport_requests_urgency", "transport_requests", ["urgency"])
    op.create_index("ix_transport_requests_requester_id", "transport_requests", ["requester_id"])


def downgrade() -> None:
    op.drop_table("transport_requests")
