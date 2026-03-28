"""Create emergency_cases table and add is_emergency to campaigns.

Revision ID: 051
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "051"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_emergency flag to campaigns table
    op.add_column(
        "campaigns",
        sa.Column(
            "is_emergency",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "emergency_cases",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "rescuer_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "campaign_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("photos", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("amount_needed_cents", sa.Integer(), nullable=False),
        sa.Column("amount_raised_cents", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("deadline", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", index=True),
        sa.Column("urgency", sa.String(20), nullable=False, server_default="high", index=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('active', 'funded', 'closed', 'expired')",
            name="chk_emergency_status_valid",
        ),
        sa.CheckConstraint(
            "urgency IN ('high', 'critical')",
            name="chk_emergency_urgency_valid",
        ),
        sa.CheckConstraint(
            "currency IN ('USD', 'PYG')",
            name="chk_emergency_currency_valid",
        ),
        sa.CheckConstraint(
            "amount_needed_cents > 0",
            name="chk_emergency_amount_positive",
        ),
        sa.Index("ix_emergency_cases_deadline", "deadline"),
    )


def downgrade() -> None:
    op.drop_table("emergency_cases")
    op.drop_column("campaigns", "is_emergency")
