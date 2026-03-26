"""Alembic migration: Create contact_submissions table.

Stores public contact form and animal inquiry submissions with
soft-delete support and follow-up tracking.
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

FORM_TYPES = ["general", "animal_inquiry"]


def upgrade() -> None:
    op.create_table(
        "contact_submissions",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column("form_type", sa.String(50), nullable=False),
        sa.Column("visitor_name", sa.String(100), nullable=False),
        sa.Column("visitor_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("responded_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Check constraint for valid form types
    op.create_check_constraint(
        "chk_contact_submissions_form_type",
        "contact_submissions",
        sa.column("form_type").in_(FORM_TYPES),
    )

    # Indexes for common queries
    op.create_index(
        "ix_contact_submissions_form_type",
        "contact_submissions",
        ["form_type"],
    )
    op.create_index(
        "ix_contact_submissions_created_at",
        "contact_submissions",
        ["created_at"],
    )
    op.create_index(
        "ix_contact_submissions_visitor_email",
        "contact_submissions",
        ["visitor_email"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_contact_submissions_visitor_email",
        table_name="contact_submissions",
    )
    op.drop_index(
        "ix_contact_submissions_created_at",
        table_name="contact_submissions",
    )
    op.drop_index(
        "ix_contact_submissions_form_type",
        table_name="contact_submissions",
    )
    op.drop_constraint(
        "chk_contact_submissions_form_type",
        "contact_submissions",
        type_="check",
    )
    op.drop_table("contact_submissions")
