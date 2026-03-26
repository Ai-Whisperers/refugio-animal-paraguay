"""Create follow_ups table for post-adoption tracking.

Revision ID: 012
Revises: 010
"""

import sqlalchemy as sa
from alembic import op

revision = "012c"
down_revision = "012b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "follow_ups",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "adoption_request_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("adoption_requests.id", name="fk_follow_ups_adoption_request_id"),
            nullable=False,
        ),
        sa.Column("scheduled_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "day_offset",
            sa.Integer,
            nullable=False,
            comment="Days after adoption (7, 30, 90, 365)",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("survey_sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("survey_completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "welfare_score",
            sa.SmallInteger,
            nullable=True,
            comment="1-5 welfare assessment",
        ),
        sa.Column(
            "satisfaction_score",
            sa.SmallInteger,
            nullable=True,
            comment="1-5 adopter satisfaction",
        ),
        sa.Column("comments", sa.Text, nullable=True),
        sa.Column("photo_url", sa.Text, nullable=True),
        sa.Column("issues_noted", sa.Text, nullable=True),
        sa.Column("return_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("return_reason_code", sa.String(30), nullable=True),
        sa.Column("return_notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_follow_ups_adoption_request_id",
        "follow_ups",
        ["adoption_request_id"],
    )
    op.create_index("ix_follow_ups_scheduled_date", "follow_ups", ["scheduled_date"])
    op.create_index("ix_follow_ups_status", "follow_ups", ["status"])


def downgrade() -> None:
    op.drop_index("ix_follow_ups_status", table_name="follow_ups")
    op.drop_index("ix_follow_ups_scheduled_date", table_name="follow_ups")
    op.drop_index("ix_follow_ups_adoption_request_id", table_name="follow_ups")
    op.drop_table("follow_ups")
