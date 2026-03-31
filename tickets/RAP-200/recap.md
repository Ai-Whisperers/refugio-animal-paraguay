# RAP-200 Recap

## Outcome

Delivered the Meta Cloud WhatsApp Business API service layer for Refugio Animal Paraguay. The pre-existing Twilio integration was preserved for backward compatibility. The new `MetaWhatsAppService` is disabled-by-default (controlled via `META_WHATSAPP_ENABLED` env var) and uses an injected `httpx.AsyncClient` for full testability.

## Acceptance Criteria — Final Status

- [x] `MetaWhatsAppService` client added to `src/notifications/meta_whatsapp_service.py`
- [x] Sends text messages and template messages via Meta Cloud API Graph endpoint
- [x] Disabled-by-default (returns True without calling API when disabled)
- [x] Phone number normalisation (strips leading '+')
- [x] Config settings added to `src/config.py` (6 new fields)
- [x] 23 unit tests — all passing
- [x] PR #326 opened against develop

## Key Learnings

- httpx injection pattern (passing client into constructor) is the cleanest way to unit-test async HTTP services without monkey-patching
- Meta Cloud API does not accept '+' prefix on phone numbers — must strip before sending
- Disabled-by-default design avoids accidental API calls in development/staging without credentials

## Validation Evidence

- Tests: 23 unit tests passing, 0 failing
- Linting: ruff clean (zero warnings)
- Type check: mypy clean
- Format: black clean
- PR: #326 — feature/RAP-200-meta-whatsapp-business-api-setup → develop
