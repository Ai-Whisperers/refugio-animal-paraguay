# RAP-204 Plan

## Objective
Enable two-way WhatsApp conversation handling via a Meta Cloud API webhook, so the shelter can receive messages from users and auto-acknowledge them.

## Acceptance Criteria
- [ ] GET /webhooks/whatsapp verifies Meta's hub.verify_token challenge
- [ ] POST /webhooks/whatsapp receives and processes incoming messages
- [ ] HMAC-SHA256 signature verification on POST payloads
- [ ] Auto-acknowledgement template sent to sender on receipt
- [ ] Always returns 200 OK (prevents Meta retry storms)
- [ ] 13 unit tests passing

## Complexity Assessment
**Track**: Simple — new router file, no DB changes, uses existing MetaWhatsAppService

## Approach
1. Create src/api/whatsapp_webhook.py with GET (challenge) + POST (messages) endpoints
2. Add to app.py router registration
3. Write unit tests

## Dependencies
- RAP-200: MetaWhatsAppService (done)
- Config: meta_whatsapp_verify_token already in Settings (done)
