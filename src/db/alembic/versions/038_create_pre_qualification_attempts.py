"""Create pre_qualification_attempts table for analytics tracking.

Revision ID: 038
Revises: 037
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pre_qualification_attempts",
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
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("outcome", sa.String(20), nullable=False, index=True),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("failed_requirement_types", sa.Text, nullable=True),
        sa.Column("mandatory_failures", sa.Integer, nullable=False, server_default="0"),
        sa.Column("preferred_failures", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.CheckConstraint(
            "outcome IN ('qualified', 'disqualified')",
            name="chk_pqa_outcome",
        ),
        sa.CheckConstraint(
            "score >= 0 AND score <= 100",
            name="chk_pqa_score_range",
        ),
    )


def downgrade() -> None:
    op.drop_table("pre_qualification_attempts")
