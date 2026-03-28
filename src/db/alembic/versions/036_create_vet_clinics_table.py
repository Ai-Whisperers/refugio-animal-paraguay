"""Create vet_clinics table for partner clinic registration.

Revision ID: 036
Revises: 031
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "036"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vet_clinics",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        # Identity
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("license_number", sa.String(100), nullable=True, unique=True),
        # Contact
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("contact_person", sa.String(200), nullable=False),
        # Address
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column(
            "department",
            sa.String(100),
            nullable=True,
            comment="Paraguayan department (state)",
        ),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        # Capabilities
        sa.Column(
            "specialties",
            sa.Text,
            nullable=True,
            comment="Comma-separated list of specialties",
        ),
        sa.Column(
            "accepts_emergencies",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
        # Partnership
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("partnership_start", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("partnership_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        # Timestamps
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
        # Constraints
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'suspended', 'inactive')",
            name="chk_vet_clinics_status",
        ),
    )

    op.create_index("ix_vet_clinics_status", "vet_clinics", ["status"])
    op.create_index("ix_vet_clinics_city", "vet_clinics", ["city"])


def downgrade() -> None:
    op.drop_index("ix_vet_clinics_city", table_name="vet_clinics")
    op.drop_index("ix_vet_clinics_status", table_name="vet_clinics")
    op.drop_table("vet_clinics")
