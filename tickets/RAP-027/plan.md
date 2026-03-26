# RAP-027 Plan

## Objective
Implement an email notification service that integrates with the event bus to send transactional emails for key domain events.

## Description
The shelter needs email notifications for critical workflows: adoption status changes, donation confirmations, animal intake alerts, and volunteer shift updates. The service uses SMTP (with SendGrid/Mailgun support) and subscribes to domain events via the existing event bus for async, non-blocking delivery. Jinja2 templates provide branded, consistent emails.

## Acceptance Criteria
- [ ] Email service supports SMTP and SendGrid API backends
- [ ] Email templates exist for adoption status changes, donation receipts, and welcome emails
- [ ] Service subscribes to event bus events and sends emails asynchronously
- [ ] Failed email deliveries are logged with error details (no silent failures)
- [ ] Email sending is disabled in test environment by default
- [ ] Configuration via environment variables (SMTP host, port, credentials, from address)
- [ ] Notification queue processes events without blocking the main request cycle
- [ ] Unit test coverage >= 90% for email service and template rendering
- [ ] Integration test covers event-to-email flow end-to-end

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified — N/A (new feature)
- [x] Solution affects ≤3 files — NO (8+ files)
- [ ] Change impact ≤10 lines — NO
- [ ] Low risk of side effects — moderate risk (event bus integration)
- [x] Solution pattern is well-understood — YES

**Assessment result**: Complex — new subsystem with event bus integration, templates, config, and tests

## Approach
1. Add email config settings to Settings class
2. Create email service module (src/notifications/) with SMTP backend
3. Create Jinja2 email templates for key events
4. Create event handlers that subscribe to domain events and trigger emails
5. Register handlers during app startup (lifespan)
6. Write unit tests for service, templates, and handlers
7. Write integration test for event-to-email flow

## Dependencies
- Depends on: Event bus (RAP-023, DONE)
- Depends on: Auth system (RAP-007, DONE)

## Risks
- Risk: SMTP connection failures in CI → Mitigation: Mock SMTP in tests, configurable disable
- Risk: Email delivery blocking requests → Mitigation: Async via event bus, fire-and-forget
