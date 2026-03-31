"""Create email_lists and email_list_members tables.

Revision ID: 083
Revises: 082
Create Date: 2026-03-29

Introduces email list management infrastructure for EPIC-44 Email Campaign
System. Staff can create named lists, segment by user type, and manage
subscribers with GDPR-compliant unsubscribe tokens.
"""

from alembic import op
import sqlalchemy as sa

revision = "083"
down_revision = "082"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_lists",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "list_type",
            sa.String(50),
            nullable=False,
            server_default="general",
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_by_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_email_lists_list_type", "email_lists", ["list_type"])
    op.create_index("ix_email_lists_status", "email_lists", ["status"])
    op.create_index("ix_email_lists_created_by_id", "email_lists", ["created_by_id"])

    op.create_table(
        "email_list_members",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "email_list_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("email_lists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="subscribed",
        ),
        sa.Column("unsubscribe_token", sa.String(64), nullable=False, unique=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "subscribed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_email_list_members_email_list_id",
        "email_list_members",
        ["email_list_id"],
    )
    op.create_index(
        "ix_email_list_members_email",
        "email_list_members",
        ["email"],
    )
    op.create_index(
        "ix_email_list_members_status",
        "email_list_members",
        ["status"],
    )
    op.create_unique_constraint(
        "uq_email_list_member_email",
        "email_list_members",
        ["email_list_id", "email"],
    )


def downgrade() -> None:
    op.drop_table("email_list_members")
    op.drop_table("email_lists")
