"""Create return_requests table for adoption returns.

Revision ID: 055
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "055"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "return_requests",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "adoption_request_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey(
                "adoption_requests.id",
                name="fk_return_requests_adoption_request_id",
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column(
            "animal_condition",
            sa.String(20),
            nullable=False,
            server_default="healthy",
        ),
        sa.Column(
            "is_emergency",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("staff_notes", sa.Text, nullable=True),
        sa.Column(
            "requested_by",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", name="fk_return_requests_requested_by"),
            nullable=True,
        ),
        sa.Column(
            "requested_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_return_requests_adoption",
        "return_requests",
        ["adoption_request_id"],
    )
    op.create_index(
        "ix_return_requests_status",
        "return_requests",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("return_requests")
