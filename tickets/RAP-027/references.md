# RAP-027 References

## Key Files
- `src/events/bus.py` — Event bus dispatcher
- `src/events/types.py` — EventType enum, DomainEvent
- `src/events/domain_events.py` — Concrete event classes
- `src/config.py` — Application settings
- `src/app.py` — App factory and lifespan

## New Files (to create)
- `src/notifications/__init__.py`
- `src/notifications/service.py` — EmailService class
- `src/notifications/templates.py` — Template rendering
- `src/notifications/handlers.py` — Event bus handlers
- `src/notifications/templates/` — Jinja2 email templates
- `tests/unit/test_email_service.py`
- `tests/unit/test_email_templates.py`
- `tests/unit/test_notification_handlers.py`
- `tests/integration/test_email_notifications.py`
