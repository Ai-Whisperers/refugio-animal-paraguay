"""Add show_in_public flag to donors for campaign social proof privacy.

Revision ID: 019
Revises: 018
Create Date: 2026-03-26
"""

import sqlalchemy as sa
from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add show_in_public column — defaults to true (donors are visible by default)
    op.add_column(
        "donors",
        sa.Column(
            "show_in_public",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.create_index("ix_donors_show_in_public", "donors", ["show_in_public"])


def downgrade() -> None:
    op.drop_index("ix_donors_show_in_public", "donors")
    op.drop_column("donors", "show_in_public")
