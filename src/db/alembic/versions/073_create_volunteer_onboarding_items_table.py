"""Create volunteer_onboarding_items table (RAP-642).

Revision ID: 073
Revises: 072
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "073"
down_revision = "072"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "volunteer_onboarding_items",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "volunteer_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("volunteer_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_key", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "completed",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "completed_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_volunteer_onboarding_items_volunteer_id",
        "volunteer_onboarding_items",
        ["volunteer_id"],
    )
    op.create_unique_constraint(
        "uq_volunteer_onboarding_item",
        "volunteer_onboarding_items",
        ["volunteer_id", "item_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_volunteer_onboarding_item",
        "volunteer_onboarding_items",
        type_="unique",
    )
    op.drop_index(
        "ix_volunteer_onboarding_items_volunteer_id",
        table_name="volunteer_onboarding_items",
    )
    op.drop_table("volunteer_onboarding_items")
