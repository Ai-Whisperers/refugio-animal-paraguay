"""Create cms_contents table for content management.

Revision ID: 047
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "047"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cms_contents",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("content_type", sa.String(30), nullable=False, index=True),
        sa.Column("slug", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.String(500), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'draft'"),
            index=True,
        ),
        sa.Column("featured_image_url", sa.String(500), nullable=True),
        sa.Column("meta_description", sa.String(300), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column(
            "author_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "content_type IN ('page', 'blog_post', 'success_story', 'announcement', 'faq')",
            name="chk_cms_content_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="chk_cms_status_valid",
        ),
        sa.CheckConstraint(
            "length(title) >= 1",
            name="chk_cms_title_not_empty",
        ),
        sa.CheckConstraint(
            "length(title) <= 300",
            name="chk_cms_title_max_len",
        ),
        sa.Index("ix_cms_contents_type_status", "content_type", "status"),
        sa.Index("ix_cms_contents_published_at", "published_at"),
    )


def downgrade() -> None:
    op.drop_table("cms_contents")
