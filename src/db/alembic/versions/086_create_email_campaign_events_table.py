"""Create email_campaign_events table.

Revision ID: 086
Revises: 085
Create Date: 2026-03-29

Adds open/click tracking for email campaigns (EPIC-44 S4 RAP-218).
Events are recorded via public pixel and redirect endpoints embedded
in outbound campaign emails.
"""

import sqlalchemy as sa
from alembic import op

revision = "086"
down_revision = "085"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_campaign_events",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "campaign_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("email_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(10),
            nullable=False,
            comment="open or click",
        ),
        sa.Column("recipient_email", sa.String(320), nullable=True),
        sa.Column("clicked_url", sa.Text(), nullable=True),
        sa.Column(
            "variant",
            sa.String(1),
            nullable=True,
            comment="a or b for A/B test variant attribution",
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_email_campaign_events_campaign_id",
        "email_campaign_events",
        ["campaign_id"],
    )
    op.create_index(
        "ix_email_campaign_events_recipient_email",
        "email_campaign_events",
        ["recipient_email"],
    )
    op.create_index(
        "ix_email_campaign_events_campaign_type",
        "email_campaign_events",
        ["campaign_id", "event_type"],
    )


def downgrade() -> None:
    op.drop_table("email_campaign_events")
