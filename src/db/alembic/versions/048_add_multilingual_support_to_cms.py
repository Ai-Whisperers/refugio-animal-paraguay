"""Add multilingual support to cms_contents table.

Revision ID: 048
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "048"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column with default 'es' (Spanish — primary language for Paraguay)
    op.add_column(
        "cms_contents",
        sa.Column(
            "language",
            sa.String(5),
            nullable=False,
            server_default=sa.text("'es'"),
        ),
    )

    # Add translation_status column to track translation progress
    op.add_column(
        "cms_contents",
        sa.Column(
            "translation_status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'original'"),
        ),
    )

    # Add source_content_id for linking translations to original content
    op.add_column(
        "cms_contents",
        sa.Column(
            "source_content_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("cms_contents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Drop old unique constraint on slug alone
    op.drop_constraint("cms_contents_slug_key", "cms_contents", type_="unique")

    # Create new unique constraint on (slug, language)
    op.create_unique_constraint(
        "uq_cms_contents_slug_language",
        "cms_contents",
        ["slug", "language"],
    )

    # Add index on language for filtering
    op.create_index("ix_cms_contents_language", "cms_contents", ["language"])

    # Add index on source_content_id for finding translations
    op.create_index(
        "ix_cms_contents_source_content_id",
        "cms_contents",
        ["source_content_id"],
    )

    # Add check constraint for valid language codes
    op.create_check_constraint(
        "chk_cms_language_valid",
        "cms_contents",
        "language IN ('es', 'en', 'de', 'nl')",
    )

    # Add check constraint for valid translation status
    op.create_check_constraint(
        "chk_cms_translation_status_valid",
        "cms_contents",
        "translation_status IN ('original', 'translated', 'pending', 'outdated')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_cms_translation_status_valid", "cms_contents", type_="check")
    op.drop_constraint("chk_cms_language_valid", "cms_contents", type_="check")
    op.drop_index("ix_cms_contents_source_content_id", "cms_contents")
    op.drop_index("ix_cms_contents_language", "cms_contents")
    op.drop_constraint("uq_cms_contents_slug_language", "cms_contents", type_="unique")
    op.create_unique_constraint("cms_contents_slug_key", "cms_contents", ["slug"])
    op.drop_column("cms_contents", "source_content_id")
    op.drop_column("cms_contents", "translation_status")
    op.drop_column("cms_contents", "language")
