"""Seed data for core animal and adoption tables.

Provides initial test data for development and staging environments:
- 5 sample animals with varied species and statuses
- 2 adopters with complete profiles
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import sqlalchemy as sa
from alembic import op

# Revision identifiers
revision = "seed_001"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Insert seed data for animals and adopters."""

    # Get current table objects
    animals_table = sa.table(
        "animals",
        sa.column("id", sa.UUID),
        sa.column("name", sa.String),
        sa.column("species", sa.String),
        sa.column("status", sa.String),
        sa.column("birth_date", sa.Date),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.TIMESTAMP),
        sa.column("updated_at", sa.TIMESTAMP),
    )

    adopters_table = sa.table(
        "adopters",
        sa.column("id", sa.UUID),
        sa.column("full_name", sa.String),
        sa.column("email", sa.String),
        sa.column("phone", sa.String),
        sa.column("address", sa.Text),
        sa.column("gdpr_consent_at", sa.TIMESTAMP),
        sa.column("created_at", sa.TIMESTAMP),
        sa.column("updated_at", sa.TIMESTAMP),
    )

    # Sample animals
    animals_data = [
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440001"),
            "name": "Buddy",
            "species": "dog",
            "status": "available",
            "birth_date": date.today() - timedelta(days=730),  # ~2 years old
            "description": "Golden Retriever mix, friendly and energetic, excellent with families",
        },
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440002"),
            "name": "Luna",
            "species": "cat",
            "status": "available",
            "birth_date": date.today() - timedelta(days=365),  # ~1 year old
            "description": "Siamese mix, vocal and affectionate, prefers quiet homes",
        },
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440003"),
            "name": "Max",
            "species": "dog",
            "status": "foster",
            "birth_date": date.today() - timedelta(days=180),  # ~6 months old
            "description": "Border Collie puppy, high energy, needs experienced handler",
        },
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440004"),
            "name": "Whiskers",
            "species": "cat",
            "status": "quarantine",
            "birth_date": date.today() - timedelta(days=60),  # ~2 months old
            "description": "Tabby kitten, shy but playful, will warm up to patient adopters",
        },
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440005"),
            "name": "Rex",
            "species": "dog",
            "status": "under_treatment",
            "birth_date": date.today() - timedelta(days=1095),  # ~3 years old
            "description": "German Shepherd, recovering from injury, calm temperament",
        },
    ]

    # Sample adopters
    adopters_data = [
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655441001"),
            "full_name": "Juan Carlos López",
            "email": "juan.lopez@example.com",
            "phone": "+595 21 123456",
            "address": "Barrio San Lorenzo, Asunción, Paraguay",
            "gdpr_consent_at": datetime.now(timezone.utc),
        },
        {
            "id": uuid.UUID("550e8400-e29b-41d4-a716-446655441002"),
            "full_name": "Maria Elena García",
            "email": "maria.garcia@example.com",
            "phone": "+595 21 654321",
            "address": "Barrio Ñemby, Encarnación, Paraguay",
            "gdpr_consent_at": datetime.now(timezone.utc),
        },
    ]

    # Insert animals
    for animal in animals_data:
        op.execute(
            sa.insert(animals_table).values(
                id=animal["id"],
                name=animal["name"],
                species=animal["species"],
                status=animal["status"],
                birth_date=animal["birth_date"],
                description=animal["description"],
            )
        )

    # Insert adopters
    for adopter in adopters_data:
        op.execute(
            sa.insert(adopters_table).values(
                id=adopter["id"],
                full_name=adopter["full_name"],
                email=adopter["email"],
                phone=adopter["phone"],
                address=adopter["address"],
                gdpr_consent_at=adopter["gdpr_consent_at"],
            )
        )


def downgrade() -> None:
    """Remove seed data."""

    # Delete in reverse order of insertion (respecting FKs)
    op.execute(
        "DELETE FROM adoption_requests WHERE adopter_id IN (SELECT id FROM adopters WHERE email IN ('juan.lopez@example.com', 'maria.garcia@example.com'))"
    )
    op.execute(
        "DELETE FROM adopters WHERE email IN ('juan.lopez@example.com', 'maria.garcia@example.com')"
    )
    op.execute(
        "DELETE FROM animals WHERE name IN ('Buddy', 'Luna', 'Max', 'Whiskers', 'Rex')"
    )
