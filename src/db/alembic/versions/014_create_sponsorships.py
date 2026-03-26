"""Alembic migration: Create sponsorship_tiers and sponsorships tables.

- Creates sponsorship_tiers reference table (Bronze/Silver/Gold) with seed data
- Creates sponsorships table linking donors to animals via tiers
- Adds indexes for efficient sponsor dashboard queries
"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None

# Seed data for sponsorship tiers
_TIER_SEEDS = [
    {
        "level": "bronze",
        "name": "Bronze Sponsor",
        "amount_cents": 1000,
        "currency": "USD",
        "benefits": {
            "includes_updates": True,
            "includes_certificate": False,
            "includes_visit": False,
            "description": "Monthly status update about your sponsored animal",
        },
        "display_order": 1,
    },
    {
        "level": "silver",
        "name": "Silver Sponsor",
        "amount_cents": 2500,
        "currency": "USD",
        "benefits": {
            "includes_updates": True,
            "includes_certificate": True,
            "includes_visit": False,
            "description": "Monthly photo update + digital adoption certificate",
        },
        "display_order": 2,
    },
    {
        "level": "gold",
        "name": "Gold Sponsor",
        "amount_cents": 5000,
        "currency": "USD",
        "benefits": {
            "includes_updates": True,
            "includes_certificate": True,
            "includes_visit": True,
            "description": "Monthly video update + certificate + annual visit to the shelter",
        },
        "display_order": 3,
    },
]


def upgrade() -> None:
    """Create sponsorship_tiers and sponsorships tables, then seed tier data."""

    # ------------------------------------------------------------------
    # TABLE: sponsorship_tiers
    # Reference table for the three sponsorship tiers (Bronze/Silver/Gold).
    # Seeded at migration time; Stripe price IDs populated via admin panel.
    # ------------------------------------------------------------------
    op.create_table(
        "sponsorship_tiers",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("amount_cents", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("stripe_price_id_monthly", sa.String(255), nullable=True),
        sa.Column("stripe_price_id_annual", sa.String(255), nullable=True),
        sa.Column("benefits", sa.JSON, nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "level IN ('bronze', 'silver', 'gold')",
            name="chk_sponsorship_tiers_level",
        ),
        sa.UniqueConstraint("level", name="uq_sponsorship_tiers_level"),
    )
    op.create_index(
        "ix_sponsorship_tiers_level",
        "sponsorship_tiers",
        ["level"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # TABLE: sponsorships
    # Instance table — one row per active or historical sponsorship.
    # ------------------------------------------------------------------
    op.create_table(
        "sponsorships",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            server_default=sa.func.gen_random_uuid(),
            primary_key=True,
        ),
        sa.Column(
            "donor_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("donors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "tier_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("sponsorship_tiers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "frequency",
            sa.String(10),
            nullable=False,
            server_default="monthly",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column(
            "total_contributed_cents",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ended_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "frequency IN ('monthly', 'annual')",
            name="chk_sponsorships_frequency",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'cancelled', 'completed')",
            name="chk_sponsorships_status",
        ),
        sa.UniqueConstraint(
            "stripe_subscription_id",
            name="uq_sponsorships_stripe_subscription_id",
        ),
    )
    op.create_index("ix_sponsorships_donor_id", "sponsorships", ["donor_id"])
    op.create_index("ix_sponsorships_animal_id", "sponsorships", ["animal_id"])
    op.create_index("ix_sponsorships_tier_id", "sponsorships", ["tier_id"])
    op.create_index("ix_sponsorships_status", "sponsorships", ["status"])
    op.create_index(
        "ix_sponsorships_stripe_subscription_id",
        "sponsorships",
        ["stripe_subscription_id"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # SEED: Insert the three sponsorship tiers
    # ------------------------------------------------------------------
    tiers_table = sa.table(
        "sponsorship_tiers",
        sa.column("level"),
        sa.column("name"),
        sa.column("amount_cents"),
        sa.column("currency"),
        sa.column("benefits"),
        sa.column("display_order"),
    )
    op.bulk_insert(tiers_table, _TIER_SEEDS)


def downgrade() -> None:
    """Drop sponsorships and sponsorship_tiers tables."""
    op.drop_table("sponsorships")
    op.drop_table("sponsorship_tiers")
