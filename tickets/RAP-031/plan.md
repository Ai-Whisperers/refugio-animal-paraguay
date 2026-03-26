# RAP-031 Plan

## Objective
Build a public adoption application form that allows visitors to apply to adopt an animal.

## Description
Visitors browsing available animals need a way to submit an adoption application. This includes a public-facing form that collects applicant info (name, email, phone, message) and a lightweight backend endpoint that handles the submission without requiring authentication.

## Acceptance Criteria
- [ ] Public adoption application endpoint (POST /public/adoption-applications)
- [ ] Accepts applicant name, email, phone, message, animal_id, GDPR consent
- [ ] Creates adopter record (or finds existing by email)
- [ ] Creates adoption request in pending status
- [ ] Frontend form page at /animals/[id]/apply
- [ ] Form validation (required fields, email format)
- [ ] Success/error feedback to user
- [ ] Link from animal browsing to application form
- [ ] No authentication required for submission

## Complexity Assessment
**Track**: Complex Implementation
**Assessment result**: Complex — backend endpoint + frontend form with validation

## Approach
1. Create public adoption application schema and endpoint
2. Build frontend form page with validation
3. Build public animal browsing page and detail page
4. Lint and build validation

## Dependencies
- Depends on: RAP-028 (scaffold), animals/adopters/adoption_requests models (pre-V1)

## Risks
- Risk: Spam submissions → Mitigation: rate limiting on endpoint
