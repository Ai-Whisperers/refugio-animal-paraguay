# RAP-003 References

## Key Files
- `pyproject.toml` — dependency manifest
- `src/config.py` — Settings (to create)
- `src/db/session.py` — async session factory (to create)
- `src/app.py` — FastAPI entrypoint (to create)
- `src/api/health.py` — health route (to create)
- `tests/unit/test_config.py` — Settings unit tests (to create)
- `tests/integration/test_health.py` — health endpoint integration tests (to create)

## Related Tickets
- RAP-001: Core DB schema (Alembic migration)
- RAP-002: SQLAlchemy ORM models

## External Resources
- FastAPI lifespan docs: https://fastapi.tiangolo.com/advanced/events/
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- pydantic-settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
