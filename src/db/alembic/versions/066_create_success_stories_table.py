"""Create success_stories table.

Revision ID: 066
Revises: 065
"""

import sqlalchemy as sa
from alembic import op

revision = "066"
down_revision = "065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "success_stories",
        sa.Column("id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("animal_id", sa.UUID(as_uuid=True), sa.ForeignKey("animals.id", ondelete="SET NULL"), nullable=True),
        sa.Column("adopter_name", sa.String(200), nullable=False),
        sa.Column("story_text", sa.Text, nullable=False),
        sa.Column("quote", sa.Text, nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_success_stories_animal_id", "success_stories", ["animal_id"])
    op.create_index("ix_success_stories_published_at", "success_stories", ["published_at"])
    op.create_index("ix_success_stories_is_featured", "success_stories", ["is_featured"])
    op.create_index("ix_success_stories_created_at", "success_stories", ["created_at"])


def downgrade() -> None:
    op.drop_table("success_stories")
