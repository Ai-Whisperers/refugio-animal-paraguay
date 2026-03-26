"""Alembic migration: Create core animal and adoption tables.

Implements the foundation schema for Refugio Animal Paraguay:
- animals: animal records with status lifecycle
- adopters: adopter profiles with GDPR consent tracking
- adoption_requests: adoption application workflow

Status pattern: Use VARCHAR with CHECK constraint initially, migrate to
proper PostgreSQL enum once values stabilize (risk mitigation per ADR-001).

EXCLUDE constraint: Prevents duplicate active (status='pending') requests
per animal at the database level.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create animals, adopters, adoption_requests tables."""

    # ============================================================
    # TABLE: animals
    # Purpose: Animal records with species, status, and medical info
    # ============================================================
    op.create_table(
        "animals",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "species",
            sa.String(50),
            nullable=False,
            server_default="dog",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="intake",
        ),
        sa.Column("birth_date", sa.Date, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('intake', 'quarantine', 'available', 'foster', "
            "'under_treatment', 'adopted', 'deceased')",
            name="chk_animals_status",
        ),
        sa.CheckConstraint(
            "species IN ('dog', 'cat', 'other')",
            name="chk_animals_species",
        ),
    )

    # Indexes for common queries
    op.create_index("idx_animals_status", "animals", ["status"])
    op.create_index("idx_animals_created_at", "animals", ["created_at"])

    # ============================================================
    # TABLE: adopters
    # Purpose: Adopter profiles with GDPR consent tracking
    # ============================================================
    op.create_table(
        "adopters",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("gdpr_consent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "email ~* '^[^@]+@[^@]+\\.[^@]+$'",
            name="chk_adopters_email_format",
        ),
    )

    # Indexes for common queries
    op.create_index("idx_adopters_email", "adopters", ["email"])
    op.create_index("idx_adopters_created_at", "adopters", ["created_at"])

    # ============================================================
    # TABLE: adoption_requests
    # Purpose: Adoption application workflow and status tracking
    # ============================================================
    op.create_table(
        "adoption_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("animal_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("adopter_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("decided_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'cancelled')",
            name="chk_adoption_requests_status",
        ),
        sa.ForeignKeyConstraint(
            ["animal_id"],
            ["animals.id"],
            name="fk_adoption_requests_animal_id",
        ),
        sa.ForeignKeyConstraint(
            ["adopter_id"],
            ["adopters.id"],
            name="fk_adoption_requests_adopter_id",
        ),
    )

    # Indexes for common queries
    op.create_index(
        "idx_adoption_requests_animal_id", "adoption_requests", ["animal_id"]
    )
    op.create_index(
        "idx_adoption_requests_adopter_id", "adoption_requests", ["adopter_id"]
    )
    op.create_index("idx_adoption_requests_status", "adoption_requests", ["status"])
    op.create_index(
        "idx_adoption_requests_created_at", "adoption_requests", ["created_at"]
    )

    # EXCLUDE constraint: One active (pending) request per animal
    # Prevents duplicate pending applications for the same animal
    op.execute("""
        ALTER TABLE adoption_requests
        ADD CONSTRAINT uq_adoption_requests_one_pending_per_animal
        EXCLUDE USING GIST (
            animal_id WITH =,
            (CASE WHEN status = 'pending' THEN 1 ELSE 0 END) WITH =
        )
        WHERE (status = 'pending');
    """)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_constraint(
        "uq_adoption_requests_one_pending_per_animal",
        "adoption_requests",
    )
    op.drop_table("adoption_requests")
    op.drop_table("adopters")
    op.drop_table("animals")
