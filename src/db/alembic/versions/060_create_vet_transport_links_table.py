"""Create vet_transport_links table.

Revision ID: 060
Revises: 036
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "060"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vet_transport_links",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "transport_request_id",
            sa.Uuid(),
            sa.ForeignKey("transport_requests.id"),
            nullable=False,
        ),
        sa.Column("vet_visit_id", sa.Uuid(), sa.ForeignKey("vet_visits.id"), nullable=False),
        sa.Column("animal_id", sa.Uuid(), sa.ForeignKey("animals.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("pickup_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dropoff_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transport_request_id", "vet_visit_id", name="uq_transport_vet_visit"),
    )

    op.create_index(
        "ix_vet_transport_links_transport_id", "vet_transport_links", ["transport_request_id"]
    )
    op.create_index("ix_vet_transport_links_vet_visit_id", "vet_transport_links", ["vet_visit_id"])
    op.create_index("ix_vet_transport_links_animal_id", "vet_transport_links", ["animal_id"])


def downgrade() -> None:
    op.drop_table("vet_transport_links")
