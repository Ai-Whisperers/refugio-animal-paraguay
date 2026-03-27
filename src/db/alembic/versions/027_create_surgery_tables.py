"""Create surgery and post_op_checks tables.

Revision ID: 027
Revises: 026
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "027"
down_revision = ("025", "026")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "surgeries",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("surgery_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("surgery_status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column("veterinarian_name", sa.String(255), nullable=False),
        sa.Column("scheduled_date", sa.Date, nullable=False),
        sa.Column("performed_date", sa.Date, nullable=True),
        sa.Column("anesthesia_type", sa.String(50), nullable=True),
        sa.Column("anesthesia_notes", sa.Text, nullable=True),
        sa.Column("procedure_description", sa.Text, nullable=True),
        sa.Column("outcome", sa.String(50), nullable=True),
        sa.Column("outcome_notes", sa.Text, nullable=True),
        sa.Column("complications", sa.Text, nullable=True),
        sa.Column("weight_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("recovery_notes", sa.Text, nullable=True),
        sa.Column("follow_up_date", sa.Date, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_surgeries_animal_id", "surgeries", ["animal_id"])
    op.create_index("ix_surgeries_scheduled_date", "surgeries", ["scheduled_date"])

    op.create_table(
        "post_op_checks",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "surgery_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("surgeries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("scheduled_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("completed_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("checked_by", sa.String(255), nullable=True),
        sa.Column("temperature_celsius", sa.Numeric(4, 1), nullable=True),
        sa.Column("pain_level", sa.SmallInteger, nullable=True),
        sa.Column("appetite", sa.String(50), nullable=True),
        sa.Column("mobility", sa.String(50), nullable=True),
        sa.Column("wound_condition", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("concerns", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_post_op_checks_surgery_id", "post_op_checks", ["surgery_id"])


def downgrade() -> None:
    op.drop_table("post_op_checks")
    op.drop_table("surgeries")
