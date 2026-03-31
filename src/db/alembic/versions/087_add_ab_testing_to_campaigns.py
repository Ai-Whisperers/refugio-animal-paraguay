"""Add A/B testing columns to email_campaigns.

Revision ID: 087
Revises: 086
Create Date: 2026-03-29

Adds subject_a, subject_b, and ab_ratio columns to support A/B testing of
email subject lines. When subject_b is set, recipients are split by ab_ratio
(default 0.5) and each variant is tracked separately via EventType variant field.
"""

import sqlalchemy as sa
from alembic import op

revision = "087"
down_revision = "086"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "email_campaigns",
        sa.Column(
            "subject_a",
            sa.String(255),
            nullable=True,
            comment="Subject line for variant A (or the only subject when not A/B testing)",
        ),
    )
    op.add_column(
        "email_campaigns",
        sa.Column(
            "subject_b",
            sa.String(255),
            nullable=True,
            comment="Subject line for variant B. When set, A/B test mode is active.",
        ),
    )
    op.add_column(
        "email_campaigns",
        sa.Column(
            "ab_ratio",
            sa.Numeric(4, 3),
            nullable=False,
            server_default="0.500",
            comment="Fraction of recipients assigned to variant A (0.0-1.0). Remainder gets variant B.",
        ),
    )


def downgrade() -> None:
    op.drop_column("email_campaigns", "ab_ratio")
    op.drop_column("email_campaigns", "subject_b")
    op.drop_column("email_campaigns", "subject_a")
