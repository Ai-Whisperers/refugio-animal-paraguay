"""Create user_consents table for GDPR consent tracking.

Revision ID: 009
Revises: 008
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = None  # Handled by migration ordering
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_consents",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("consent_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "opt_in_date",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("opt_out_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "method", sa.String(30), nullable=False, server_default="user_self_service"
        ),
        sa.Column(
            "granted_by_staff_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
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
        sa.UniqueConstraint("user_id", "consent_type", name="uq_user_consent_type"),
    )

    # Check constraints for enum validation
    op.execute(
        """ALTER TABLE user_consents ADD CONSTRAINT chk_consent_type
        CHECK (consent_type IN ('marketing_email', 'newsletter', 'sms_updates',
                                'event_invitations', 'donation_receipts'))"""
    )
    op.execute(
        """ALTER TABLE user_consents ADD CONSTRAINT chk_consent_status
        CHECK (status IN ('active', 'revoked'))"""
    )
    op.execute(
        """ALTER TABLE user_consents ADD CONSTRAINT chk_consent_method
        CHECK (method IN ('user_self_service', 'email_link', 'staff_assisted', 'import_batch'))"""
    )


def downgrade() -> None:
    op.drop_table("user_consents")
