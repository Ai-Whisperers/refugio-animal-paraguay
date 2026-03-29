# RAP-202 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 03:08

## Current Focus
Implementing MetaWhatsAppAdoptionHandler — subscribe to ADOPTION_STATUS_CHANGED, DB lookup adopter info, send template via MetaWhatsAppService.

## Technical State
- MetaWhatsAppService exists at src/notifications/meta_whatsapp_service.py (send_template method)
- WhatsApp template registry at src/db/models/whatsapp_template.py (RAP-201)
- Existing whatsapp_handlers.py uses Twilio WhatsAppService, has broken adoption handler (payload.get("adopter_phone") never set)
- _lookup_adopter_phone helper exists but not called in current adoption handler
- Event payload for ADOPTION_STATUS_CHANGED: old_status, new_status, notes — NO adopter info
- aggregate_id on the event IS the adoption_request_id → use for DB lookup

## Next Steps
1. Write MetaWhatsAppAdoptionHandler
2. Wire in app.py
3. Write unit tests

## Blockers
None
