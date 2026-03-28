"""Create foster_placements table (RAP-191).

Revision ID: 076
Revises: 075
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "076"
down_revision = "075"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "foster_placements",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "foster_profile_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("foster_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_foster_placements_foster_profile_id", "foster_placements", ["foster_profile_id"]
    )
    op.create_index("ix_foster_placements_animal_id", "foster_placements", ["animal_id"])
    op.create_index("ix_foster_placements_ended_at", "foster_placements", ["ended_at"])
    # Partial unique index: only one active placement (ended_at IS NULL) per animal
    op.execute("""
        CREATE UNIQUE INDEX uq_foster_placement_active_animal
        ON foster_placements (animal_id)
        WHERE ended_at IS NULL
        """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_foster_placement_active_animal")
    op.drop_index("ix_foster_placements_ended_at", "foster_placements")
    op.drop_index("ix_foster_placements_animal_id", "foster_placements")
    op.drop_index("ix_foster_placements_foster_profile_id", "foster_placements")
    op.drop_table("foster_placements")
