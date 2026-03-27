"""Create animal_updates and sponsor_update_preferences tables.

Revision ID: 018
Revises: 017
Create Date: 2026-03-26
"""

import sqlalchemy as sa
from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # animal_updates: staff publishes updates about individual animals
    op.create_table(
        "animal_updates",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("animal_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("published_by_user_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("update_type", sa.String(20), nullable=False, server_default="general"),
        sa.Column("milestone_type", sa.String(50), nullable=True),
        sa.Column("photo_urls", sa.JSON, nullable=True, server_default="[]"),
        sa.Column(
            "published_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["animal_id"], ["animals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["published_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "update_type IN ('health', 'behavior', 'milestone', 'general')",
            name="chk_animal_updates_update_type",
        ),
    )
    op.create_index("ix_animal_updates_animal_id", "animal_updates", ["animal_id"])
    op.create_index(
        "ix_animal_updates_published_by_user_id",
        "animal_updates",
        ["published_by_user_id"],
    )

    # sponsor_update_preferences: per-sponsorship notification frequency settings
    op.create_table(
        "sponsor_update_preferences",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("sponsorship_id", sa.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column(
            "notification_enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "notification_frequency",
            sa.String(20),
            nullable=False,
            server_default="immediate",
        ),
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
        sa.ForeignKeyConstraint(
            ["sponsorship_id"], ["sponsorships.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "notification_frequency IN "
            "('immediate', 'daily_digest', 'weekly_digest', 'monthly_digest')",
            name="chk_sponsor_update_preferences_frequency",
        ),
    )
    op.create_index(
        "ix_sponsor_update_preferences_sponsorship_id",
        "sponsor_update_preferences",
        ["sponsorship_id"],
    )


def downgrade() -> None:
    op.drop_table("sponsor_update_preferences")
    op.drop_table("animal_updates")
