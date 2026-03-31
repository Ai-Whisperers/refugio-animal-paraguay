"""Create whatsapp_templates table (RAP-201).

Revision ID: 081
Revises: 080
Create Date: 2026-03-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "081"
down_revision: str | None = "080"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_templates",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(512), nullable=False),
        sa.Column("language_code", sa.String(10), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("header_text", sa.Text, nullable=True),
        sa.Column("body_text", sa.Text, nullable=False),
        sa.Column("footer_text", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("meta_template_id", sa.String(255), nullable=True, unique=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
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
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("name", "language_code", name="uq_whatsapp_templates_name_lang"),
        sa.CheckConstraint(
            "category IN ('authentication', 'marketing', 'utility')",
            name="chk_whatsapp_templates_category",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'paused', 'deleted')",
            name="chk_whatsapp_templates_status",
        ),
    )
    op.create_index("ix_whatsapp_templates_name", "whatsapp_templates", ["name"])
    op.create_index("ix_whatsapp_templates_status", "whatsapp_templates", ["status"])
    op.create_index(
        "ix_whatsapp_templates_name_lang",
        "whatsapp_templates",
        ["name", "language_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_whatsapp_templates_name_lang", table_name="whatsapp_templates")
    op.drop_index("ix_whatsapp_templates_status", table_name="whatsapp_templates")
    op.drop_index("ix_whatsapp_templates_name", table_name="whatsapp_templates")
    op.drop_table("whatsapp_templates")
