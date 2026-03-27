"""Create vet_referrals table.

Revision ID: 029
Revises: 028
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vet_referrals",
        sa.Column("id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("animal_id", sa.UUID(as_uuid=True), sa.ForeignKey("animals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referred_by_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_vet_name", sa.String(255), nullable=False),
        sa.Column("external_vet_clinic", sa.String(255), nullable=True),
        sa.Column("external_vet_phone", sa.String(50), nullable=True),
        sa.Column("external_vet_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("specialty", sa.String(100), nullable=True),
        sa.Column("urgency", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("appointment_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("diagnosis", sa.Text, nullable=True),
        sa.Column("treatment_notes", sa.Text, nullable=True),
        sa.Column("follow_up_required", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("follow_up_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("actual_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_vet_referrals_animal_id", "vet_referrals", ["animal_id"])
    op.create_index("ix_vet_referrals_status", "vet_referrals", ["status"])
    op.create_index("ix_vet_referrals_urgency", "vet_referrals", ["urgency"])


def downgrade() -> None:
    op.drop_index("ix_vet_referrals_urgency", table_name="vet_referrals")
    op.drop_index("ix_vet_referrals_status", table_name="vet_referrals")
    op.drop_index("ix_vet_referrals_animal_id", table_name="vet_referrals")
    op.drop_table("vet_referrals")
