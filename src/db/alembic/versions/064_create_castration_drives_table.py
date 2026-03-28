"""Create castration_drives table.

Revision ID: 064
Revises: 063
Create Date: 2026-03-28

Stores scheduled castration drive events within campaigns. Each drive
is a single-day event at a location with capacity tracking.
"""

import sqlalchemy as sa
from alembic import op

revision = "064"
down_revision = "063"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "castration_drives",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "campaign_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("castration_campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "clinic_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_clinics.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("location_name", sa.String(300), nullable=False),
        sa.Column("location_address", sa.String(500), nullable=True),
        sa.Column("drive_date", sa.Date, nullable=False, index=True),
        sa.Column("start_time", sa.Time, nullable=True),
        sa.Column("end_time", sa.Time, nullable=True),
        sa.Column("max_capacity", sa.Integer, nullable=False),
        sa.Column(
            "registered_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "completed_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'scheduled'"),
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("contact_phone", sa.String(30), nullable=True),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("max_capacity > 0", name="chk_drive_capacity_positive"),
        sa.CheckConstraint("registered_count >= 0", name="chk_drive_registered_non_negative"),
        sa.CheckConstraint("completed_count >= 0", name="chk_drive_completed_non_negative"),
        sa.CheckConstraint(
            "status IN ('scheduled', 'in_progress', 'completed', 'cancelled')",
            name="chk_drive_status_valid",
        ),
    )


def downgrade() -> None:
    op.drop_table("castration_drives")
