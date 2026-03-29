"""Create adoption_outcomes table for EPIC-53 outcome tracking.

Adds an adoption_outcomes table that stores one aggregated outcome record
per completed adoption request. Captures outcome type (successful/returned/
rehomed/deceased/unknown), welfare and satisfaction score averages, follow-up
completion rates, and return metadata.

Revision ID: 091
Revises: 090
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "091"
down_revision = "090"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adoption_outcomes",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "adoption_request_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey(
                "adoption_requests.id",
                name="fk_adoption_outcomes_adoption_request_id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "outcome_type",
            sa.String(20),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "outcome_date",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("avg_welfare_score", sa.Float, nullable=True),
        sa.Column("avg_satisfaction_score", sa.Float, nullable=True),
        sa.Column("total_follow_ups", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_follow_ups", sa.Integer, nullable=False, server_default="0"),
        sa.Column("return_reason_code", sa.String(30), nullable=True),
        sa.Column("return_date", sa.TIMESTAMP(timezone=True), nullable=True),
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
    )

    op.create_index(
        "ix_adoption_outcomes_adoption_request_id",
        "adoption_outcomes",
        ["adoption_request_id"],
        unique=True,
    )
    op.create_index(
        "ix_adoption_outcomes_outcome_type",
        "adoption_outcomes",
        ["outcome_type"],
    )

    op.create_check_constraint(
        "chk_adoption_outcomes_outcome_type",
        "adoption_outcomes",
        "outcome_type IN ('successful', 'returned', 'rehomed', 'deceased', 'unknown')",
    )
    op.create_check_constraint(
        "chk_adoption_outcomes_avg_welfare",
        "adoption_outcomes",
        "avg_welfare_score IS NULL OR (avg_welfare_score >= 1.0 AND avg_welfare_score <= 5.0)",
    )
    op.create_check_constraint(
        "chk_adoption_outcomes_avg_satisfaction",
        "adoption_outcomes",
        "avg_satisfaction_score IS NULL OR "
        "(avg_satisfaction_score >= 1.0 AND avg_satisfaction_score <= 5.0)",
    )
    op.create_check_constraint(
        "chk_adoption_outcomes_followup_counts",
        "adoption_outcomes",
        "completed_follow_ups <= total_follow_ups",
    )


def downgrade() -> None:
    op.drop_table("adoption_outcomes")
