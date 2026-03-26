# RAP-035 References

## Key Files
- src/db/models/user.py — User model (FK target for user_consents)
- src/db/models/__init__.py — Model exports
- src/events/domain_events.py — Domain events (add consent events)
- src/events/types.py — EventType enum
- src/app.py — App factory (register consent router)

## New Files
- src/db/models/user_consent.py — UserConsent model + enums
- src/schemas/consent.py — Consent Pydantic schemas
- src/api/consents.py — Consent API router
- src/services/consent_service.py — Consent validation service
- src/db/alembic/versions/009_create_user_consents_table.py — Migration
- tests/unit/test_consent_service.py — Unit tests
- tests/integration/test_consents.py — Integration tests
