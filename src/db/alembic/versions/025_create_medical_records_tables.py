"""Create medical records tables: vet_visits, diagnoses, treatments, medications, medical_documents.

Revision ID: 025
Revises: 024
"""

import sqlalchemy as sa
from alembic import op

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- vet_visits ---
    op.create_table(
        "vet_visits",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "animal_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("veterinarian_name", sa.String(255), nullable=False),
        sa.Column("visit_type", sa.String(50), nullable=False, server_default="checkup"),
        sa.Column("visit_status", sa.String(50), nullable=False, server_default="scheduled"),
        sa.Column(
            "visit_date",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("weight_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("temperature_celsius", sa.Numeric(4, 1), nullable=True),
        sa.Column("next_visit_date", sa.Date, nullable=True),
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
    )
    op.create_index("ix_vet_visits_animal_id", "vet_visits", ["animal_id"])
    op.create_index("ix_vet_visits_visit_date", "vet_visits", ["visit_date"])

    # --- diagnoses ---
    op.create_table(
        "diagnoses",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "vet_visit_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_visits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("condition", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("severity", sa.String(50), nullable=False, server_default="moderate"),
        sa.Column("is_chronic", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_diagnoses_vet_visit_id", "diagnoses", ["vet_visit_id"])

    # --- treatments ---
    op.create_table(
        "treatments",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "diagnosis_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("diagnoses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("treatment_status", sa.String(50), nullable=False, server_default="planned"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
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
    )
    op.create_index("ix_treatments_diagnosis_id", "treatments", ["diagnosis_id"])

    # --- medications ---
    op.create_table(
        "medications",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "treatment_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("treatments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(50), nullable=False, server_default="daily"),
        sa.Column("route", sa.String(50), nullable=True),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("medication_status", sa.String(50), nullable=False, server_default="active"),
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
    )
    op.create_index("ix_medications_treatment_id", "medications", ["treatment_id"])

    # --- medical_documents ---
    op.create_table(
        "medical_documents",
        sa.Column(
            "id",
            sa.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
        ),
        sa.Column(
            "vet_visit_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("vet_visits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("document_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_medical_documents_vet_visit_id", "medical_documents", ["vet_visit_id"])


def downgrade() -> None:
    op.drop_index("ix_medical_documents_vet_visit_id")
    op.drop_table("medical_documents")
    op.drop_index("ix_medications_treatment_id")
    op.drop_table("medications")
    op.drop_index("ix_treatments_diagnosis_id")
    op.drop_table("treatments")
    op.drop_index("ix_diagnoses_vet_visit_id")
    op.drop_table("diagnoses")
    op.drop_index("ix_vet_visits_visit_date")
    op.drop_index("ix_vet_visits_animal_id")
    op.drop_table("vet_visits")
