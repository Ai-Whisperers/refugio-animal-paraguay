# RAP-201 Recap

## Outcome

Delivered the WhatsApp message template registry: ORM model, Alembic migration, Pydantic schemas, service layer (CRUD + error classes), and 5 FastAPI endpoints. Templates follow the Meta template lifecycle (pending → approved/rejected/paused/deleted). Soft-delete via `is_active=False` preserves templates for audit.

## Acceptance Criteria — Final Status

- [x] `WhatsAppTemplate` ORM model in `src/db/models/whatsapp_template.py`
- [x] Alembic migration 081 — creates `whatsapp_templates` table with UniqueConstraint, CheckConstraints, and indexes
- [x] Pydantic schemas: Create, Update, Response, ListResponse
- [x] Service layer: `create_template`, `get_template`, `list_templates`, `update_template`, `delete_template`
- [x] Error classes: `WhatsAppTemplateNotFoundError`, `WhatsAppTemplateDuplicateError`
- [x] 5 FastAPI endpoints at `/api/whatsapp/templates` (staff/admin auth)
- [x] Duplicate detection (name + language_code unique constraint + service-level guard)
- [x] Paginated list with status/category/is_active filters; page_size capped at 100
- [x] Soft-delete (is_active=False); admin-only
- [x] 14 unit tests — all passing
- [x] PR #327 opened against develop

## Key Learnings

- Patching the ORM class with MagicMock breaks SQLAlchemy's `select()` — use `side_effect` on `db.refresh` to simulate DB-populated attributes instead
- `raise HTTPException(...) from exc` is required for ruff B904 compliance inside `except` blocks
- ruff auto-sort (I001) fires after any new import is added — always run `ruff check --fix` before final push

## Validation Evidence

- Tests: 14 unit tests passing, 0 failing
- Linting: ruff clean (zero warnings)
- Type check: mypy clean
- Format: black clean
- PR: #327 — feature/RAP-201-message-template-registry → develop
