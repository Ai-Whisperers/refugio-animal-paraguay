"""069: Create home_visits table.

Revision ID: 069
Revises: 068
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "069"
down_revision = "068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "home_visits",
        sa.Column("id", sa.UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), primary_key=True),
        sa.Column("adoption_request_id", sa.UUID(as_uuid=True), sa.ForeignKey("adoption_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("address", sa.Text, nullable=False),
        sa.Column("staff_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'scheduled'")),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("photos", sa.JSON, nullable=True),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_check_constraint(
        "chk_home_visit_status_valid",
        "home_visits",
        "status IN ('scheduled', 'completed', 'cancelled')",
    )

    op.create_index("ix_home_visits_adoption_request_id", "home_visits", ["adoption_request_id"])
    op.create_index("ix_home_visits_staff_id", "home_visits", ["staff_id"])
    op.create_index("ix_home_visits_status", "home_visits", ["status"])
    op.create_index("ix_home_visits_scheduled_at", "home_visits", ["scheduled_at"])
    op.create_index("ix_home_visits_adoption_status", "home_visits", ["adoption_request_id", "status"])


def downgrade() -> None:
    op.drop_table("home_visits")
