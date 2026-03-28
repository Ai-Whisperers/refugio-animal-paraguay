"""Create survey_distributions table.

Revision ID: 061
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "061"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "survey_distributions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "survey_id",
            sa.Uuid(),
            sa.ForeignKey("surveys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=True),
        sa.Column("recipient_phone", sa.String(30), nullable=True),
        sa.Column("delivery_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("sent_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_survey_distributions_survey_id", "survey_distributions", ["survey_id"])
    op.create_index("ix_survey_distributions_channel", "survey_distributions", ["channel"])
    op.create_index("ix_survey_distributions_status", "survey_distributions", ["delivery_status"])


def downgrade() -> None:
    op.drop_table("survey_distributions")
