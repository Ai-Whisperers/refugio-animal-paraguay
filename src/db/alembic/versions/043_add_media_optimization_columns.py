"""Add optimization columns to media table.

Revision ID: 043
Revises: 036
Create Date: 2026-03-27
"""

import sqlalchemy as sa

from alembic import op

revision = "043"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "media",
        sa.Column(
            "has_optimized",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "media",
        sa.Column(
            "has_thumbnail",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "media",
        sa.Column(
            "optimization_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "media",
        sa.Column("optimized_path", sa.Text, nullable=True),
    )
    op.add_column(
        "media",
        sa.Column("thumbnail_path", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("media", "thumbnail_path")
    op.drop_column("media", "optimized_path")
    op.drop_column("media", "optimization_status")
    op.drop_column("media", "has_thumbnail")
    op.drop_column("media", "has_optimized")
