"""Add SENACSA registration number to animals table.

Adds senacsa_registration_number (nullable Text) for Paraguayan animal
registration compliance (SENACSA = Servicio Nacional de Calidad y Salud Animal).

Revision ID: 090
Revises: 089
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "090"
down_revision = "089"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "animals",
        sa.Column(
            "senacsa_registration_number",
            sa.String(100),
            nullable=True,
            comment="SENACSA (Servicio Nacional de Calidad y Salud Animal) registration number",
        ),
    )
    op.create_index(
        "ix_animals_senacsa_registration_number",
        "animals",
        ["senacsa_registration_number"],
    )


def downgrade() -> None:
    op.drop_index("ix_animals_senacsa_registration_number", table_name="animals")
    op.drop_column("animals", "senacsa_registration_number")
