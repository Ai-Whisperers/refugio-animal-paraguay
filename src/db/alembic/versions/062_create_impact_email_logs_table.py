"""Create impact_email_logs table.

Revision ID: 062
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "062"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "impact_email_logs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("donor_id", sa.Uuid(), sa.ForeignKey("donors.id"), nullable=False),
        sa.Column("email_address", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("report_month", sa.Integer(), nullable=False),
        sa.Column("report_year", sa.Integer(), nullable=False),
        sa.Column("donation_total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="PYG"),
        sa.Column("animals_rescued", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("animals_adopted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("castrations_funded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medical_treatments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("opened_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.String(500), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "donor_id", "report_year", "report_month", name="uq_donor_report_period"
        ),
    )

    op.create_index("ix_impact_email_logs_donor_id", "impact_email_logs", ["donor_id"])
    op.create_index("ix_impact_email_logs_status", "impact_email_logs", ["status"])
    op.create_index(
        "ix_impact_email_logs_report_period", "impact_email_logs", ["report_year", "report_month"]
    )


def downgrade() -> None:
    op.drop_table("impact_email_logs")
