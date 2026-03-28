"""Create share_events table for share tracking analytics.

Revision ID: 049
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "049"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "share_events",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("entity_type", sa.String(20), nullable=False, index=True),
        sa.Column("entity_id", sa.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("platform", sa.String(20), nullable=False, index=True),
        sa.Column(
            "sharer_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        sa.CheckConstraint(
            "entity_type IN ('animal', 'campaign', 'story', 'blog_post')",
            name="chk_share_entity_type_valid",
        ),
        sa.CheckConstraint(
            "platform IN ('whatsapp', 'facebook', 'twitter', 'copy_link', 'native_share')",
            name="chk_share_platform_valid",
        ),
        sa.Index("ix_share_events_entity", "entity_type", "entity_id"),
        sa.Index("ix_share_events_created_date", "created_at"),
    )


def downgrade() -> None:
    op.drop_table("share_events")
