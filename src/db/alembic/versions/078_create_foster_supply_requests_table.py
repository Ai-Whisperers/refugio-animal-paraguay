"""Create foster_supply_requests table (RAP-194).

Revision ID: 078
Revises: 077
Create Date: 2026-03-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "078"
down_revision: str | None = "077"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "foster_supply_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "foster_profile_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("foster_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "placement_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("foster_placements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("supply_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("staff_notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "supply_type IN ('bedding', 'food', 'grooming', 'medication', 'other', 'toys', 'transport')",
            name="chk_foster_supply_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('approved', 'fulfilled', 'pending', 'rejected')",
            name="chk_foster_supply_status_valid",
        ),
        sa.CheckConstraint(
            "length(description) >= 10",
            name="chk_foster_supply_description_min_len",
        ),
        sa.CheckConstraint(
            "quantity IS NULL OR (quantity >= 1 AND quantity <= 999)",
            name="chk_foster_supply_quantity_range",
        ),
    )
    op.create_index(
        "ix_foster_supply_requests_foster_profile_id",
        "foster_supply_requests",
        ["foster_profile_id"],
    )
    op.create_index(
        "ix_foster_supply_requests_placement_id",
        "foster_supply_requests",
        ["placement_id"],
    )
    op.create_index(
        "ix_foster_supply_requests_status",
        "foster_supply_requests",
        ["status"],
    )
    op.create_index(
        "ix_foster_supply_requests_supply_type",
        "foster_supply_requests",
        ["supply_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_foster_supply_requests_supply_type", "foster_supply_requests")
    op.drop_index("ix_foster_supply_requests_status", "foster_supply_requests")
    op.drop_index("ix_foster_supply_requests_placement_id", "foster_supply_requests")
    op.drop_index("ix_foster_supply_requests_foster_profile_id", "foster_supply_requests")
    op.drop_table("foster_supply_requests")
