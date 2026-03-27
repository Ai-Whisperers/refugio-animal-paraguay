"""Create vaccination tables.

Revision ID: 026
Revises: 024
Create Date: 2026-03-27

Tables: vaccine_types, vaccination_schedules, vaccinations
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "026"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- vaccine_types ---
    op.create_table(
        "vaccine_types",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column(
            "target_species",
            sa.String(50),
            nullable=False,
            server_default="dog",
        ),
        sa.Column(
            "is_required",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # --- vaccination_schedules ---
    op.create_table(
        "vaccination_schedules",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "vaccine_type_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vaccine_types.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("species", sa.String(50), nullable=False),
        sa.Column("dose_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("age_weeks_min", sa.Integer, nullable=True),
        sa.Column("age_weeks_max", sa.Integer, nullable=True),
        sa.Column("interval_days", sa.Integer, nullable=True),
        sa.Column(
            "is_booster",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # --- vaccinations ---
    op.create_table(
        "vaccinations",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vaccine_type_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vaccine_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vaccination_status",
            sa.String(50),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("scheduled_date", sa.Date, nullable=False),
        sa.Column("administered_date", sa.Date, nullable=True),
        sa.Column("administered_by", sa.String(255), nullable=True),
        sa.Column("batch_number", sa.String(100), nullable=True),
        sa.Column("dose_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("next_due_date", sa.Date, nullable=True),
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
    )

    # Indexes for vaccinations
    op.create_index("ix_vaccinations_animal_id", "vaccinations", ["animal_id"])
    op.create_index(
        "ix_vaccinations_vaccine_type_id", "vaccinations", ["vaccine_type_id"]
    )
    op.create_index(
        "ix_vaccinations_scheduled_date", "vaccinations", ["scheduled_date"]
    )


def downgrade() -> None:
    op.drop_table("vaccinations")
    op.drop_table("vaccination_schedules")
    op.drop_table("vaccine_types")
