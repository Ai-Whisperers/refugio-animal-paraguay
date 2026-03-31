"""Add pipeline tracking columns to adoption_requests and create stage logs.

Revision ID: 054
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "054"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add pipeline tracking columns to adoption_requests
    op.add_column(
        "adoption_requests",
        sa.Column(
            "current_stage_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey(
                "adoption_pipeline_stages.id",
                name="fk_adoption_requests_current_stage_id",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "adoption_requests",
        sa.Column(
            "current_stage_started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_adoption_requests_current_stage",
        "adoption_requests",
        ["current_stage_id"],
    )

    # Create adoption stage logs table
    op.create_table(
        "adoption_stage_logs",
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
                name="fk_stage_logs_adoption_request_id",
            ),
            nullable=False,
        ),
        sa.Column(
            "from_stage_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey(
                "adoption_pipeline_stages.id",
                name="fk_stage_logs_from_stage_id",
            ),
            nullable=True,
        ),
        sa.Column(
            "to_stage_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey(
                "adoption_pipeline_stages.id",
                name="fk_stage_logs_to_stage_id",
            ),
            nullable=True,
        ),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "transitioned_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", name="fk_stage_logs_transitioned_by"),
            nullable=True,
        ),
        sa.Column(
            "transitioned_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_stage_logs_adoption_request",
        "adoption_stage_logs",
        ["adoption_request_id", "transitioned_at"],
    )


def downgrade() -> None:
    op.drop_table("adoption_stage_logs")
    op.drop_index(
        "ix_adoption_requests_current_stage",
        table_name="adoption_requests",
    )
    op.drop_column("adoption_requests", "current_stage_started_at")
    op.drop_column("adoption_requests", "current_stage_id")
