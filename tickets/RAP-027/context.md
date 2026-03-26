# RAP-027 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Implementing email notification service with event bus integration.

## Technical State
- Event bus is operational (RAP-023)
- Domain events defined for adoption, donation, medical, volunteer, animal domains
- No email infrastructure exists yet
- Project uses Pydantic Settings for config, FastAPI lifespan for startup

## Next Steps
1. Add email settings to config.py
2. Create src/notifications/ module
3. Implement EmailService with SMTP backend
4. Create Jinja2 templates
5. Wire event handlers in app lifespan

## Blockers
- None

## Key Decisions Made
- Using aiosmtplib for async SMTP (non-blocking)
- Jinja2 for template rendering (already a FastAPI dependency via Starlette)
- Event bus subscription pattern for decoupled notification triggers
