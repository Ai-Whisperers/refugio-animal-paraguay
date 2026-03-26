# RAP-053 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26 16:15

## Current Focus
Ticket complete. PR #39 created.

## Technical State
- `src/events/domain_events.py`: Added AdoptionRequestCreated class + factory
- `src/api/adoption_requests.py`: Injects event_bus, publishes on create + status change
- `src/api/public_adoption.py`: Publishes AdoptionRequestCreated on public applications
- `src/notifications/handlers.py`: on_adoption_request_created handler + _get_staff_emails
- 2 email templates added (adoption_request_received, adoption_request_staff_alert)
- Integration conftest updated with autouse _attach_event_bus fixture
- test_email_notifications subscriber count updated 2->3

## Key Decisions Made
- Event bus fixture added to shared integration conftest (not per-test-file) since all endpoints now depend on it
- Event publishing is conditional on bus.is_running to avoid failures when bus is down
