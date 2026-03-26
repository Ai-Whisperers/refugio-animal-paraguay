# ADR-001: Core Tech Stack Selection

**Date**: 2026-03-25
**Status**: Accepted
**Deciders**: Project owner

---

## Context

Refugio Animal Paraguay needs a backend stack for an animal shelter management platform with:
- EU donor integration (SEPA, IBAN, GDPR compliance)
- Dual currency: EUR (European donors) + PYG (local Paraguayan)
- Animal records, adoptions, volunteer coordination
- Dutch owner context — EU-standard tooling preferred

## Decision

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.12 | Owner familiarity; strong async support; best-in-class Stripe/GDPR libraries |
| Framework | FastAPI | Async-native; Pydantic v2 integration; auto-generates OpenAPI docs; faster than Django REST for API-only backends |
| ORM | SQLAlchemy 2.x | Mature; supports async; works with Alembic for migrations |
| Migrations | Alembic | Standard SQLAlchemy migration tool; reversible migrations required |
| Database | PostgreSQL 16 | ACID compliance critical for financial data; UUID support; JSONB for flexible fields |
| Auth | JWT (HTTP Bearer) | Stateless; suitable for future mobile/third-party integrations |
| Payments | Stripe | EU-compliant; supports SEPA Direct Debit for recurring EU donors; PYG-to-EUR conversion path |
| CI/CD | GitHub Actions | Repository already on GitHub; no additional infra cost |

## Alternatives Considered

**Django REST Framework**: Rejected — heavier, sync-first, more boilerplate for pure API backend.
**SQLModel**: Considered as a SQLAlchemy + Pydantic shortcut, but SQLAlchemy 2.x + Pydantic v2 directly gives more control and is better documented.
**Auth0 / Supabase Auth**: Deferred — adds external dependency; JWT + fastapi-users is sufficient for MVP.

## Consequences

- All skills files (fastapi-patterns, postgresql-patterns, python-patterns) are now canonical for this stack.
- Frontend remains TBD — decouple from backend decisions.
- PYG payment processor for local donors still to be decided (ADR-002 when ready).
- Hosting TBD — EU-West region preferred for donor latency (ADR-003 when ready).

## Related ADRs

- ADR-002 (pending): PYG payment processor
- ADR-003 (pending): Hosting platform selection
