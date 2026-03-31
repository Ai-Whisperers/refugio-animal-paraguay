"""Add 'emergency' to donation target_type CHECK constraint.

Revision ID: 066
Revises: 065
"""

from alembic import op

revision = "066"
down_revision = "065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_target_type")
    op.execute(
        """
        ALTER TABLE donations ADD CONSTRAINT chk_donations_target_type
        CHECK (target_type IN ('general', 'animal', 'rescuer', 'clinic', 'campaign', 'need', 'emergency'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE donations DROP CONSTRAINT IF EXISTS chk_donations_target_type")
    op.execute(
        """
        ALTER TABLE donations ADD CONSTRAINT chk_donations_target_type
        CHECK (target_type IN ('general', 'animal', 'rescuer', 'clinic', 'campaign', 'need'))
        """
    )
