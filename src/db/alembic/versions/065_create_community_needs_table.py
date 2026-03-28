"""Create community_needs table.

Revision ID: 065
Revises: 064
Create Date: 2026-03-28

Stores community needs that donors can fund directly. Each need has
a cost goal, raised total, and auto-closes when fully funded.
"""

import sqlalchemy as sa
from alembic import op

revision = "065"
down_revision = "064"


def upgrade() -> None:
    op.create_table(
        "community_needs",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(20), nullable=False, server_default="other"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("estimated_cost_cents", sa.Integer, nullable=False),
        sa.Column("current_raised_cents", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("donor_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "creator_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_community_needs_status", "community_needs", ["status"])
    op.create_index("ix_community_needs_creator_id", "community_needs", ["creator_id"])


def downgrade() -> None:
    op.drop_index("ix_community_needs_creator_id", table_name="community_needs")
    op.drop_index("ix_community_needs_status", table_name="community_needs")
    op.drop_table("community_needs")
