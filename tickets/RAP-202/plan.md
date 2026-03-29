# RAP-202 Plan

## Objective
Send WhatsApp template notifications via Meta Cloud API when an adoption request status changes, so adopters are informed in real-time on WhatsApp.

## Description
RAP-200 set up the Meta Cloud API client and RAP-201 created the template registry. This story wires those foundations to the adoption workflow: when staff approve, reject, or cancel an adoption request, the adopter receives a WhatsApp template message (if they have a phone number on file).

## Acceptance Criteria
- [ ] `MetaWhatsAppAdoptionHandler` subscribes to `ADOPTION_STATUS_CHANGED` events
- [ ] Handler looks up adopter phone, name, and animal name from the adoption_request_id (aggregate_id)
- [ ] Handler sends a WhatsApp template message via `MetaWhatsAppService`
- [ ] Handler skips silently when adopter has no phone or Meta WhatsApp is disabled
- [ ] Handler fails gracefully (log, no re-raise) on API errors
- [ ] Unit tests cover: skip when disabled, skip when no phone, sends correct template params, graceful error handling
- [ ] Handler is registered in app.py on startup

## Complexity Assessment
**Track**: Simple — extends existing services, no schema changes, no new migrations

**Assessment result**: Simple — 2 files added (handler + tests), 1 file modified (app.py)

## Approach
1. Create `src/notifications/meta_whatsapp_adoption_handler.py`
   - Subscribe to `ADOPTION_STATUS_CHANGED`
   - DB lookup for adopter phone/name and animal name
   - Send via `MetaWhatsAppService.send_template()`
2. Wire handler in `src/app.py`
3. Add unit tests in `tests/unit/test_meta_whatsapp_adoption_handler.py`

## Dependencies
- RAP-200: MetaWhatsAppService (done)
- RAP-201: WhatsApp template registry (done)

## Risks
- Adopter may not have a phone number → handled with early return
- Meta API may be disabled in dev → handled with is_enabled check
