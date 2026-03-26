"""Add breed, size, gender columns to animals table.

Supports public browsing filters required by EPIC-11 S01 (Animal Browsing and Search).
These columns enable filtering by breed, size category, and gender on the public portal.

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
    op.add_column("animals", sa.Column("breed", sa.String(100), nullable=True))
    op.add_column(
        "animals",
        sa.Column("size", sa.String(20), nullable=True),
    )
    op.add_column(
        "animals",
        sa.Column("gender", sa.String(20), nullable=True),
    )

    # CHECK constraints to enforce valid values
    op.create_check_constraint(
        "chk_animals_size",
        "animals",
        "size IS NULL OR size IN ('small', 'medium', 'large', 'extra_large')",
    )
    op.create_check_constraint(
        "chk_animals_gender",
        "animals",
        "gender IS NULL OR gender IN ('male', 'female', 'unknown')",
    )

    # Indexes for public browsing filter performance
    op.create_index("ix_animals_breed", "animals", ["breed"])
    op.create_index("ix_animals_size", "animals", ["size"])
    op.create_index("ix_animals_gender", "animals", ["gender"])
    op.create_index("ix_animals_species", "animals", ["species"])
    op.create_index("ix_animals_status", "animals", ["status"])
    # Partial index for the most common public query: available animals
    op.execute(
        "CREATE INDEX ix_animals_available ON animals (species, gender, size) "
        "WHERE status = 'available'"
    )


def downgrade() -> None:
    """Remove breed, size, gender columns and their constraints/indexes."""
    op.execute("DROP INDEX IF EXISTS ix_animals_available")
    op.drop_index("ix_animals_status", table_name="animals")
    op.drop_index("ix_animals_species", table_name="animals")
    op.drop_index("ix_animals_gender", table_name="animals")
    op.drop_index("ix_animals_size", table_name="animals")
    op.drop_index("ix_animals_breed", table_name="animals")
    op.drop_constraint("chk_animals_gender", "animals", type_="check")
    op.drop_constraint("chk_animals_size", "animals", type_="check")
    op.drop_column("animals", "gender")
    op.drop_column("animals", "size")
    op.drop_column("animals", "breed")
