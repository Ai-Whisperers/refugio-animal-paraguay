"""Create blog_posts table.

Revision ID: 067
Revises: 066
"""

import sqlalchemy as sa
from alembic import op

revision = "067"
down_revision = "066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "blog_posts",
        sa.Column("id", sa.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(350), nullable=False, unique=True),
        sa.Column("body_html", sa.Text, nullable=False),
        sa.Column("author_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("featured_image_url", sa.String(500), nullable=True),
        sa.Column("tags", sa.JSON, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_blog_posts_slug", "blog_posts", ["slug"], unique=True)
    op.create_index("ix_blog_posts_author_id", "blog_posts", ["author_id"])
    op.create_index("ix_blog_posts_published_at", "blog_posts", ["published_at"])
    op.create_index("ix_blog_posts_is_published", "blog_posts", ["is_published"])
    op.create_index("ix_blog_posts_created_at", "blog_posts", ["created_at"])


def downgrade() -> None:
    op.drop_table("blog_posts")
