"""Alembic migration: Add intake_records table.

Tracks animal intake workflow — source, finder info, location, condition,
quarantine status, and staff who processed the intake.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create intake_records table with indexes."""

    op.create_table(
        "intake_records",
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
            unique=True,
        ),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("finder_name", sa.String(255), nullable=True),
        sa.Column("finder_email", sa.String(255), nullable=True),
        sa.Column("finder_phone", sa.String(50), nullable=True),
        sa.Column("location_found", sa.Text, nullable=True),
        sa.Column("condition_on_arrival", sa.Text, nullable=True),
        sa.Column(
            "requires_quarantine",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "intake_date",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "staff_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
        # CHECK constraint for source enum values
        sa.CheckConstraint(
            "source IN ('stray', 'surrender', 'rescue', 'transfer')",
            name="chk_intake_records_source",
        ),
    )

    # Indexes for common query patterns
    op.create_index("ix_intake_records_animal_id", "intake_records", ["animal_id"])
    op.create_index("ix_intake_records_intake_date", "intake_records", ["intake_date"])
    op.create_index("ix_intake_records_source", "intake_records", ["source"])
    op.create_index(
        "ix_intake_records_requires_quarantine",
        "intake_records",
        ["requires_quarantine"],
    )


def downgrade() -> None:
    """Drop intake_records table."""
    op.drop_index("ix_intake_records_requires_quarantine", table_name="intake_records")
    op.drop_index("ix_intake_records_source", table_name="intake_records")
    op.drop_index("ix_intake_records_intake_date", table_name="intake_records")
    op.drop_index("ix_intake_records_animal_id", table_name="intake_records")
    op.drop_table("intake_records")
