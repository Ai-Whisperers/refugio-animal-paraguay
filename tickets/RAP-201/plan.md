# RAP-201 Plan

## Objective
Create a WhatsApp message template registry — a database model + API for staff to manage and track Meta-approved template metadata.

## Description
EPIC-41 S2 — Templates must be pre-registered and approved by Meta before use. Staff need to register template names, languages, categories, and track their approval status so the MetaWhatsAppService can reference approved templates by name.

## Acceptance Criteria
- [ ] WhatsAppMessageTemplate model created (name, language, category, status, body_text, created_at, updated_at)
- [ ] Alembic migration 081 created
- [ ] Pydantic schemas: create, read, update
- [ ] API endpoints: POST /whatsapp/templates, GET /whatsapp/templates, GET /whatsapp/templates/{id}, PATCH /whatsapp/templates/{id}, DELETE /whatsapp/templates/{id}
- [ ] Staff-only auth (admin/staff role) on write endpoints
- [ ] Unit tests achieve ≥80% coverage
- [ ] ruff, black clean

## Complexity Assessment
**Track**: Complex (model + migration + schemas + router + tests, ~5 files, DB change)

## Approach
1. Create ORM model src/db/models/whatsapp_template.py
2. Create migration 081_create_whatsapp_message_templates_table.py
3. Create Pydantic schemas src/schemas/whatsapp_template.py
4. Create service src/services/whatsapp_template_service.py
5. Create router src/api/whatsapp_templates.py
6. Register router in src/app.py
7. Write tests

## Dependencies
- RAP-200 (Meta WhatsApp service) — currently in PR #326, not yet merged
- Templates exist independently; no hard runtime dependency on MetaWhatsAppService

## Risks
- Risk: Migration conflicts → Mitigation: use next available number (081)
