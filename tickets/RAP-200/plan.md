# RAP-200 Plan

## Objective
Add Meta Cloud WhatsApp Business API client as the primary WhatsApp transport, replacing Twilio for outbound messaging.

## Description
EPIC-41 S1 — The shelter needs to send WhatsApp notifications via the Meta Cloud API directly (without Twilio as intermediary). This provides lower cost, direct control over templates, and aligns with Meta's recommended integration path. The existing Twilio service remains as a fallback during transition.

## Acceptance Criteria
- [ ] Meta Cloud API configuration added to Settings (token, phone_number_id, api_version, base_url)
- [ ] `MetaWhatsAppService` created in `src/notifications/meta_whatsapp_service.py` using httpx
- [ ] Service sends text messages and template messages via Meta Graph API
- [ ] Service is disabled-by-default and safe to call when disabled (returns True)
- [ ] Unit tests achieve ≥80% coverage
- [ ] ruff, black, mypy clean

## Complexity Assessment
**Track**: Simple Fix (single service file + config additions + tests, ≤5 files, no DB changes)

**Assessment result**: Simple Fix — adds a new service class mirroring existing WhatsApp service pattern

## Approach
1. Add `meta_whatsapp_*` settings to `src/config.py`
2. Create `src/notifications/meta_whatsapp_service.py` with `MetaWhatsAppService`
3. Write tests in `tests/unit/test_meta_whatsapp_service.py`

## Dependencies
- Depends on: httpx (already in pyproject.toml ✓)
- Blocked by: nothing

## Risks
- Risk: Meta API structure changes → Mitigation: version-pin to v18.0, make configurable
