"""Create adoption_pipeline_stages table.

Revision ID: 053
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "053"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adoption_pipeline_stages",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("max_days", sa.Integer(), nullable=True),
        sa.Column(
            "color",
            sa.String(7),
            nullable=False,
            server_default="'#6B7280'",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_pipeline_stage_name"),
        sa.UniqueConstraint("position", name="uq_pipeline_stage_position"),
        sa.CheckConstraint("position > 0", name="chk_pipeline_stage_position"),
        sa.CheckConstraint(
            "max_days IS NULL OR max_days > 0",
            name="chk_pipeline_stage_max_days",
        ),
    )

    # Seed default pipeline stages
    op.execute("""
        INSERT INTO adoption_pipeline_stages (name, description, position, requires_approval, color)
        VALUES
            ('Application Review', 'Initial review of the adoption application', 1, true, '#3B82F6'),
            ('Home Visit', 'Schedule and conduct home visit assessment', 2, true, '#F59E0B'),
            ('Trial Period', 'Animal stays with adopter on a trial basis', 3, true, '#10B981'),
            ('Final Approval', 'Final approval and paperwork completion', 4, true, '#8B5CF6'),
            ('Completed', 'Adoption finalized and completed', 5, false, '#059669')
    """)


def downgrade() -> None:
    op.drop_table("adoption_pipeline_stages")
