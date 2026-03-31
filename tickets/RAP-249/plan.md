# RAP-249 Plan

## Objective
Add `?lang=es|en` support to all legal document endpoints so EU donors and international partners can read documents in English while Spanish remains the binding default.

## Description
The /legal/dpa and /legal/record-retention-policy endpoints currently return Spanish-only content. This ticket adds bilingual support via a `?lang=` query parameter, a new `GET /legal/supported-languages` discovery endpoint, and a `multilingual_legal_service` module that centralises all translation constants.

## Acceptance Criteria
- [x] `GET /legal/supported-languages` returns `default_language`, `supported_languages`, and `documents` list
- [x] `GET /legal/dpa?lang=en` returns English DPA with 9 sections
- [x] `GET /legal/dpa?lang=es` (and default) returns Spanish DPA with 9 sections
- [x] `GET /legal/record-retention-policy?lang=en` returns English document title and note
- [x] `GET /legal/record-retention-policy?lang=es` (and default) returns Spanish title and note
- [x] Unsupported `?lang=` codes fall back silently to `es`
- [x] All endpoints remain public (no auth required)
- [x] `normalise_language()` is case-insensitive and strips whitespace
- [x] Unit tests: 42 passing
- [x] Integration tests: 16 passing

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified (no i18n layer exists yet)
- [x] Solution affects ≤3 files (service + api + tests)
- [x] Low risk of side effects (additive-only, no DB changes)
- [x] Solution pattern is well-understood (query param + fallback dict)

**Assessment result**: Simple Fix — pure Python, no schema changes, additive endpoints only

## Approach
1. Create `src/services/multilingual_legal_service.py` with constants and `normalise_language()`
2. Extract English DPA sections into `legal_documents.py`; create `_DPA_BY_LANG` dispatch dict
3. Update DPA and retention-policy endpoints to accept `?lang` param
4. Add `GET /legal/supported-languages` endpoint
5. Write unit tests (service layer + endpoint via TestClient)
6. Write integration tests (httpx AsyncClient + live DB)

## Dependencies
- Depends on: RAP-247 (record retention policy endpoint, already merged)
- Blocks: nothing

## Risks
- Risk: TestClient raises RuntimeError for DB-dependent endpoints in unit tests
  → Mitigation: DB-dependent endpoint tests delegated to integration tests only
