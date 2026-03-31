"""Add rescuer_id FK to campaigns table for rescuer-created campaigns.

Revision ID: 070
Revises: 069
"""

import sqlalchemy as sa
from alembic import op

revision = "070"
down_revision = "069"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column(
            "rescuer_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("rescuer_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_campaigns_rescuer_id", "campaigns", ["rescuer_id"])
    # goal_message — short motivational text shown on the campaign page
    op.add_column(
        "campaigns",
        sa.Column("goal_message", sa.String(300), nullable=True),
    )
    # animal_ids — list of animal UUIDs involved in this campaign
    op.add_column(
        "campaigns",
        sa.Column(
            "animal_ids",
            sa.ARRAY(sa.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    # requires_approval — True for unverified rescuer campaigns
    op.add_column(
        "campaigns",
        sa.Column(
            "requires_approval",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "requires_approval")
    op.drop_column("campaigns", "animal_ids")
    op.drop_column("campaigns", "goal_message")
    op.drop_index("ix_campaigns_rescuer_id", table_name="campaigns")
    op.drop_column("campaigns", "rescuer_id")
