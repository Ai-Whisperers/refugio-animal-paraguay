# RAP-002 References

## Key Files
- `src/db/migrations/001_create_core_animal_adoption_tables.py` — schema source of truth
- `src/db/base.py` — DeclarativeBase (to create)
- `src/db/models/animal.py` — Animal model (to create)
- `src/db/models/adopter.py` — Adopter model (to create)
- `src/db/models/adoption_request.py` — AdoptionRequest model (to create)
- `src/db/models/__init__.py` — model exports (to create)
- `tests/unit/test_models.py` — unit tests (to create)

## Related Tickets
- RAP-001: Core schema migration (COMPLETED — defines column types, constraints, indexes)

## External Resources
- SQLAlchemy 2.x ORM mapped classes: https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html
- SQLAlchemy 2.x Mapped/mapped_column: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html

## Conventions (from RAP-001 / Refugio standards)
- UUID PKs: `sa.UUID(as_uuid=True)`, `server_default=func.gen_random_uuid()`
- Timestamps: `TIMESTAMP(timezone=True)`, `server_default=func.now()`
- `updated_at`: add `onupdate=func.now()` for auto-update
- Status enums: Python `enum.Enum` matching CHECK constraint values exactly
- All models use SQLAlchemy 2.x `Mapped[T]` + `mapped_column()` style — no legacy `Column()`
