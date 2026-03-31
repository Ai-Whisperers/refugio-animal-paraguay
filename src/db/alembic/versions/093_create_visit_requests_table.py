"""Create visit_requests table for EPIC-56 adopter portal visit scheduling.

Allows adopters to propose preferred visit slots that staff can confirm.

Revision ID: 093
Revises: 092
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "093"
down_revision = "092"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visit_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "adoption_request_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("adoption_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "adopter_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("adopters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("proposed_slots", sa.JSON, nullable=False),
        sa.Column("address", sa.Text, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "confirmed_home_visit_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("home_visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'cancelled', 'expired')",
            name="chk_visit_request_status_valid",
        ),
    )
    op.create_index(
        "ix_visit_requests_adoption_request_id",
        "visit_requests",
        ["adoption_request_id"],
    )
    op.create_index(
        "ix_visit_requests_adopter_id",
        "visit_requests",
        ["adopter_id"],
    )
    op.create_index(
        "ix_visit_requests_status",
        "visit_requests",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_visit_requests_status", "visit_requests")
    op.drop_index("ix_visit_requests_adopter_id", "visit_requests")
    op.drop_index("ix_visit_requests_adoption_request_id", "visit_requests")
    op.drop_table("visit_requests")
