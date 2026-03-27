"""Create phone_verification_otps table and add phone_verified columns to users.

Adds the phone_verification_otps table for storing hashed OTPs, and adds
phone_verified (bool) + phone_verified_at (timestamp) columns to users.

Revision ID: 034
Revises: 031
Create Date: 2026-03-27
"""

import sqlalchemy as sa
from alembic import op

revision = "034"
down_revision = "031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create phone_verification_otps table
    op.create_table(
        "phone_verification_otps",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column(
            "otp_hash",
            sa.String(255),
            nullable=False,
            comment="bcrypt hash of the 6-digit OTP",
        ),
        sa.Column(
            "attempted_count",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_phone_verification_otps_user_id", "phone_verification_otps", ["user_id"])
    op.create_index("ix_phone_verification_otps_phone", "phone_verification_otps", ["phone"])
    op.create_index(
        "ix_phone_verification_otps_created_at",
        "phone_verification_otps",
        ["created_at"],
    )

    # Add phone_verified and phone_verified_at to users
    op.add_column(
        "users",
        sa.Column(
            "phone_verified",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column("phone_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "phone_verified_at")
    op.drop_column("users", "phone_verified")
    op.drop_table("phone_verification_otps")
