# RAP-004 References

## Key Files
- `src/db/models/animal.py` — Animal ORM model, AnimalSpecies, AnimalStatus enums
- `src/db/session.py` — get_db async dependency
- `src/app.py` — router registration target
- `src/api/health.py` — pattern reference for router structure
- `tests/unit/test_config.py` — unit test style reference
- `tests/integration/test_health.py` — integration test pattern reference

## Related Tickets
- RAP-001: Animal schema migration
- RAP-002: Alembic scaffold
- RAP-003: FastAPI app scaffold (dependency)
- RAP-005: Adopters CRUD (follows same pattern)

## External Resources
- FastAPI path params with UUID: https://fastapi.tiangolo.com/tutorial/path-params/
- SQLAlchemy async select: https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html
