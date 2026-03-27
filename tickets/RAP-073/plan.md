# RAP-073 Plan

## Objective
Integrate WhatsApp Business API (via Twilio) to send templated notification messages for adoption status updates and volunteer shift reminders.

## Description
Paraguay is a WhatsApp-dominant culture. Adopters and volunteers prefer WhatsApp over email for receiving updates. This story adds a WhatsApp notification channel to the existing notification infrastructure, sending pre-approved templated messages via the Twilio WhatsApp API. The integration is send-only (no chatbot). It complements the existing email notification handlers without replacing them.

## Acceptance Criteria
- [ ] WhatsApp service class wraps Twilio API; fails gracefully when disabled/unconfigured
- [ ] Config settings added: twilio_account_sid, twilio_auth_token, twilio_whatsapp_from, whatsapp_enabled
- [ ] Event handlers subscribe to adoption status changes and volunteer shift events
- [ ] WhatsApp templates defined for: adoption status update, shift confirmation, shift reminder, shift cancellation
- [ ] Unit tests cover service (enabled/disabled), template rendering, handler logic
- [ ] Integration tests verify end-to-end message dispatch via mocked Twilio client
- [ ] No real Twilio credentials committed; all credentials from env vars

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — requires new service class, config additions, event handler registration, and test coverage across multiple layers.

## Approach
1. Add Twilio to pyproject.toml dependencies
2. Extend Settings with WhatsApp/Twilio config fields
3. Create `src/notifications/whatsapp_service.py` — WhatsApp sender wrapping Twilio REST client
4. Create `src/notifications/whatsapp_handlers.py` — Event handlers that dispatch WhatsApp messages
5. Register handlers in app lifespan
6. Write unit and integration tests

## Dependencies
- Depends on: EPIC-6 S01 (Email Notification System, DONE), event bus (DONE)
- Blocked by: None

## Risks
- Twilio credentials required at runtime; tests must mock the Twilio client
- WhatsApp templates require Meta approval in production; service must handle template-not-approved gracefully
