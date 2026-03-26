"""Alembic migration: Add animal photo support.

- Adds primary_photo_url (nullable TEXT) to animals table
- Creates animal_photos table for multi-photo galleries

Photos are URL-only: the shelter uploads images to Cloudinary externally;
the API stores the resulting URLs.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add primary_photo_url to animals; create animal_photos table."""

    # ------------------------------------------------------------------
    # COLUMN: animals.primary_photo_url
    # Quick-display photo — populated by staff after upload to Cloudinary
    # ------------------------------------------------------------------
    op.add_column(
        "animals",
        sa.Column("primary_photo_url", sa.Text, nullable=True),
    )

    # ------------------------------------------------------------------
    # TABLE: animal_photos
    # Gallery photos for an animal; ordered by display_order, created_at
    # ------------------------------------------------------------------
    op.create_table(
        "animal_photos",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("caption", sa.Text, nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_animal_photos_animal_id", "animal_photos", ["animal_id"])


def downgrade() -> None:
    """Reverse: drop animal_photos table; drop primary_photo_url column."""
    op.drop_index("ix_animal_photos_animal_id", table_name="animal_photos")
    op.drop_table("animal_photos")
    op.drop_column("animals", "primary_photo_url")
