"""Create rescuer_verification_requests table.

Revision ID: 046
Revises: 036
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "046"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rescuer_verification_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "rescuer_profile_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("rescuer_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("evidence_url", sa.String(500), nullable=True),
        sa.Column("evidence_notes", sa.Text, nullable=True),
        sa.Column(
            "reviewer_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewer_notes", sa.Text, nullable=True),
        sa.Column(
            "reviewed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
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
        sa.CheckConstraint(
            "method IN ('whatsapp', 'social', 'manual')",
            name="chk_verification_method_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="chk_verification_status_valid",
        ),
    )


def downgrade() -> None:
    op.drop_table("rescuer_verification_requests")
