"""Create adoption_requirements table.

Revision ID: 037
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "adoption_requirements",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("requirement_type", sa.String(30), nullable=False),
        sa.Column("value", sa.JSON, nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
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
        sa.CheckConstraint(
            "requirement_type IN ("
            "'yard_required', 'no_children_under', 'experience_required', "
            "'home_type', 'max_hours_alone', 'other_pets_ok', "
            "'housing_status', 'income_requirement')",
            name="chk_adoption_requirements_type",
        ),
    )
    op.create_index(
        "ix_adoption_requirements_animal_type",
        "adoption_requirements",
        ["animal_id", "requirement_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_adoption_requirements_animal_type")
    op.drop_table("adoption_requirements")
