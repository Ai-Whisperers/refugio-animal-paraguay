# RAP-042 Plan — EXEMPLAR: Good Plan

_This is a calibration example showing a well-structured ticket plan._

---

## Objective

Add email validation for EU donor registration that enforces RFC 5322 compliance and checks for disposable email domains.

## Description

EU donors registering through the platform occasionally use disposable email addresses, which causes failed GDPR consent confirmations and bounced donation receipts. We need validation at registration time to catch these before they enter the database.

## Acceptance Criteria

- [ ] Email is validated against RFC 5322 pattern on the registration form (frontend)
- [ ] Email is validated server-side before saving (defense in depth)
- [ ] Disposable email domains (mailinator.com, guerrilla.com, etc.) are rejected with a specific error message
- [ ] Valid EU email formats (including .eu TLDs and subdomains) are accepted
- [ ] Error messages follow WHAT+WHY+HOW format from quality-standards.md
- [ ] Unit tests cover: valid email, invalid format, disposable domain, edge cases (empty, null)

## Complexity Assessment

**Track**: Simple Fix

### Criteria Evaluation
- [x] Single, clear root cause: missing validation on donor email field
- [x] Solution affects ≤3 files: `DonorForm.tsx`, `donor_service.py`, `test_donor_validation.py`
- [x] Change impact ≤10 lines: adding a validation call + importing validator
- [x] Low risk of side effects: additive change, not modifying existing flows
- [x] Known pattern: email validation is standard; `email-validator` library exists

**Assessment result**: Simple Fix — additive validation, no architectural changes needed.

## Approach

1. Add `email-validator` library (Python) / `validator.js` (TypeScript)
2. Create `validate_donor_email(email: str) -> None` in `src/utils/validation.py`
3. Call validation in `DonorService.register()` before DB write
4. Add frontend validation in `DonorForm.tsx` for immediate feedback
5. Write unit tests

## Dependencies

- Depends on: None
- Blocked by: Nothing

## Risks

- Risk: Overly strict validation rejects valid international email formats → Mitigation: Test with EU-format emails (firstname.lastname@domain.eu, firstname+tag@domain.co.uk) before shipping
