"""Alembic migration: Add gender and size columns to animals table.

Adds optional gender and size fields to support public browsing filters.
Both columns are nullable to maintain backward compatibility with existing records.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "animals",
        sa.Column(
            "gender",
            sa.String(50),
            nullable=True,
            comment="male, female, or unknown",
        ),
    )
    op.add_column(
        "animals",
        sa.Column(
            "size",
            sa.String(50),
            nullable=True,
            comment="small, medium, large, or extra_large",
        ),
    )
    # Add CHECK constraints matching the enum values
    op.execute(
        "ALTER TABLE animals ADD CONSTRAINT chk_animals_gender "
        "CHECK (gender IS NULL OR gender IN ('male', 'female', 'unknown'))"
    )
    op.execute(
        "ALTER TABLE animals ADD CONSTRAINT chk_animals_size "
        "CHECK (size IS NULL OR size IN ('small', 'medium', 'large', 'extra_large'))"
    )
    # Index for common filter queries
    op.create_index("ix_animals_gender", "animals", ["gender"])
    op.create_index("ix_animals_size", "animals", ["size"])
    op.create_index("ix_animals_species", "animals", ["species"])
    op.create_index("ix_animals_status", "animals", ["status"])


def downgrade() -> None:
    op.drop_index("ix_animals_status", table_name="animals")
    op.drop_index("ix_animals_species", table_name="animals")
    op.drop_index("ix_animals_size", table_name="animals")
    op.drop_index("ix_animals_gender", table_name="animals")
    op.execute("ALTER TABLE animals DROP CONSTRAINT chk_animals_size")
    op.execute("ALTER TABLE animals DROP CONSTRAINT chk_animals_gender")
    op.drop_column("animals", "size")
    op.drop_column("animals", "gender")
