"""Add breed, size, gender columns to animals table.

Supports public browsing filters required by EPIC-11 S01 (Animal Browsing and Search).
These columns enable filtering by breed, size category, and gender on the public portal.

Idempotent: uses IF NOT EXISTS / IF EXISTS guards because some columns may
already exist from prior partial migration attempts.

Revision: 008
"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add breed, size, gender columns with CHECK constraints and indexes."""
    conn = op.get_bind()

    # Add columns only if they don't already exist
    conn.execute(
        sa.text(
            "ALTER TABLE animals ADD COLUMN IF NOT EXISTS breed VARCHAR(100)"
        )
    )
    conn.execute(
        sa.text(
            "ALTER TABLE animals ADD COLUMN IF NOT EXISTS size VARCHAR(20)"
        )
    )
    conn.execute(
        sa.text(
            "ALTER TABLE animals ADD COLUMN IF NOT EXISTS gender VARCHAR(20)"
        )
    )

    # CHECK constraints (idempotent — drop if exists, then create)
    conn.execute(
        sa.text("ALTER TABLE animals DROP CONSTRAINT IF EXISTS chk_animals_size")
    )
    conn.execute(
        sa.text(
            "ALTER TABLE animals ADD CONSTRAINT chk_animals_size "
            "CHECK (size IS NULL OR size IN ('small', 'medium', 'large', 'extra_large'))"
        )
    )
    conn.execute(
        sa.text("ALTER TABLE animals DROP CONSTRAINT IF EXISTS chk_animals_gender")
    )
    conn.execute(
        sa.text(
            "ALTER TABLE animals ADD CONSTRAINT chk_animals_gender "
            "CHECK (gender IS NULL OR gender IN ('male', 'female', 'unknown'))"
        )
    )

    # Indexes (idempotent — CREATE INDEX IF NOT EXISTS)
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_animals_breed ON animals (breed)")
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_animals_size ON animals (size)")
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_animals_gender ON animals (gender)")
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS ix_animals_species ON animals (species)")
    )
    # Partial index for the most common public query: available animals
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_animals_available "
            "ON animals (species, gender, size) WHERE status = 'available'"
        )
    )


def downgrade() -> None:
    """Remove breed column and partial index (size/gender preserved for other uses)."""
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_animals_available"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_animals_breed"))
    op.drop_column("animals", "breed")
