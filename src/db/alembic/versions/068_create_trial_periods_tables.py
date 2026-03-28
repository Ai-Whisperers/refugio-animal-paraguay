"""Create trial_periods and trial_check_ins tables.

Revision ID: 068
Revises: 067
"""

from alembic import op
import sqlalchemy as sa

revision = "068"
down_revision = "067"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trial_periods",
        sa.Column("id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("adoption_request_id", sa.UUID(as_uuid=True), sa.ForeignKey("adoption_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("check_in_schedule", sa.JSON, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_trial_periods_adoption_request_id", "trial_periods", ["adoption_request_id"])
    op.create_index("ix_trial_periods_status", "trial_periods", ["status"])
    op.execute(
        "ALTER TABLE trial_periods ADD CONSTRAINT chk_trial_status_valid "
        "CHECK (status IN ('active', 'passed', 'failed', 'extended'))"
    )

    op.create_table(
        "trial_check_ins",
        sa.Column("id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("trial_period_id", sa.UUID(as_uuid=True), sa.ForeignKey("trial_periods.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_number", sa.Integer, nullable=False),
        sa.Column("how_is_animal", sa.Text, nullable=False),
        sa.Column("photos", sa.JSON, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("issues", sa.Text, nullable=True),
        sa.Column("happiness_rating", sa.Integer, nullable=False),
        sa.Column("has_issues", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_trial_check_ins_trial_period_id", "trial_check_ins", ["trial_period_id"])
    op.execute(
        "ALTER TABLE trial_check_ins ADD CONSTRAINT chk_checkin_rating_range "
        "CHECK (happiness_rating >= 1 AND happiness_rating <= 5)"
    )
    op.execute(
        "ALTER TABLE trial_check_ins ADD CONSTRAINT chk_checkin_day_positive "
        "CHECK (day_number > 0)"
    )


def downgrade() -> None:
    op.drop_table("trial_check_ins")
    op.drop_table("trial_periods")
