"""Create clinic_services table for veterinary service catalog.

Each partner clinic can maintain a catalog of services with pricing
in PYG (and optionally EUR for international donors).

Revision ID: 037
Revises: 036
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinic_services",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "clinic_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "category",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'other'"),
        ),
        sa.Column(
            "price_pyg",
            sa.Integer,
            nullable=False,
            comment="Price in Paraguayan Guarani",
        ),
        sa.Column(
            "price_eur",
            sa.Numeric(10, 2),
            nullable=True,
            comment="Optional price in EUR for international donors",
        ),
        sa.Column(
            "duration_minutes",
            sa.Integer,
            nullable=True,
            comment="Estimated duration in minutes",
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
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
            "category IN ('consultation', 'vaccination', 'surgery', 'dental', "
            "'diagnostic', 'grooming', 'emergency', 'preventive', 'other')",
            name="chk_clinic_services_category",
        ),
        sa.CheckConstraint("price_pyg >= 0", name="chk_clinic_services_price_pyg"),
        sa.CheckConstraint(
            "price_eur IS NULL OR price_eur >= 0",
            name="chk_clinic_services_price_eur",
        ),
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="chk_clinic_services_duration",
        ),
    )

    # Indexes
    op.create_index(
        "ix_clinic_services_clinic_id",
        "clinic_services",
        ["clinic_id"],
    )
    op.create_index(
        "ix_clinic_services_clinic_id_category",
        "clinic_services",
        ["clinic_id", "category"],
    )
    op.create_index(
        "ix_clinic_services_active",
        "clinic_services",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_clinic_services_active", table_name="clinic_services")
    op.drop_index(
        "ix_clinic_services_clinic_id_category", table_name="clinic_services"
    )
    op.drop_index("ix_clinic_services_clinic_id", table_name="clinic_services")
    op.drop_table("clinic_services")
