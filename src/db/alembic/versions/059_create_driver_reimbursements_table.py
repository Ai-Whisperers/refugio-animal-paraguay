"""Create driver_reimbursements table.

Revision ID: 059
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "059"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "driver_reimbursements",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "transport_request_id",
            sa.Uuid(),
            sa.ForeignKey("transport_requests.id"),
            nullable=False,
        ),
        sa.Column("driver_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expense_type", sa.String(30), nullable=False, server_default="fuel"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PYG"),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("receipt_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_driver_reimbursements_status", "driver_reimbursements", ["status"])
    op.create_index("ix_driver_reimbursements_driver_id", "driver_reimbursements", ["driver_id"])
    op.create_index(
        "ix_driver_reimbursements_transport_id", "driver_reimbursements", ["transport_request_id"]
    )


def downgrade() -> None:
    op.drop_table("driver_reimbursements")
