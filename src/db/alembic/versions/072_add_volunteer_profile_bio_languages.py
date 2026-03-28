"""Add bio and languages_spoken to volunteer_profiles.

Revision ID: 072
Revises: 071
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "072"
down_revision = "071"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "volunteer_profiles",
        sa.Column("bio", sa.String(500), nullable=True),
    )
    op.add_column(
        "volunteer_profiles",
        sa.Column("languages_spoken", sa.JSON, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("volunteer_profiles", "languages_spoken")
    op.drop_column("volunteer_profiles", "bio")
