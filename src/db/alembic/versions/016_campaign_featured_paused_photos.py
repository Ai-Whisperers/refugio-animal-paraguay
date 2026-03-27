"""Alembic migration: Add featured flag, paused/archived status, and photo_urls to campaigns.

Changes:
- campaigns.featured BOOLEAN NOT NULL DEFAULT false
- campaigns.photo_urls TEXT[] NOT NULL DEFAULT '{}'
- Update CHECK constraint on status to include 'paused' and 'archived'
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add featured, photo_urls columns; broaden status CHECK constraint."""

    # Add featured column — controls prominence on public fundraising page
    op.add_column(
        "campaigns",
        sa.Column(
            "featured",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Add photo_urls array — multiple campaign photos beyond the primary image
    op.add_column(
        "campaigns",
        sa.Column(
            "photo_urls",
            sa.ARRAY(sa.Text),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )

    # Index for fast featured-campaign queries on the public page
    op.create_index(
        "ix_campaigns_featured_status",
        "campaigns",
        ["featured", "status"],
    )

    # Drop the old status CHECK constraint and create a broader one.
    # The original constraint only allowed: draft, active, completed, cancelled.
    # We add: paused, archived (keep cancelled for backward compatibility).
    op.drop_constraint("chk_campaigns_status", "campaigns")
    op.create_check_constraint(
        "chk_campaigns_status",
        "campaigns",
        "status IN ('draft', 'active', 'paused', 'completed', 'archived', 'cancelled')",
    )


def downgrade() -> None:
    """Revert featured/photo_urls columns and restore original status CHECK."""

    op.drop_index("ix_campaigns_featured_status", table_name="campaigns")
    op.drop_column("campaigns", "featured")
    op.drop_column("campaigns", "photo_urls")

    # Restore original status constraint (note: data with paused/archived
    # statuses must be migrated first or downgrade will fail)
    op.drop_constraint("chk_campaigns_status", "campaigns")
    op.create_check_constraint(
        "chk_campaigns_status",
        "campaigns",
        "status IN ('draft', 'active', 'completed', 'cancelled')",
    )
