"""Create surveys and survey_responses tables.

Revision ID: 056
Revises: 036
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "056"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "surveys",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("questions", JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("start_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "survey_responses",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("survey_id", sa.Uuid(), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("respondent_email", sa.String(255), nullable=True),
        sa.Column("respondent_user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("answers", JSONB(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_survey_responses_survey_id", "survey_responses", ["survey_id"])
    op.create_unique_constraint(
        "uq_survey_responses_survey_email", "survey_responses", ["survey_id", "respondent_email"]
    )


def downgrade() -> None:
    op.drop_table("survey_responses")
    op.drop_table("surveys")
