# RAP-151 Plan

## Objective
Create SEPA mandate creation UI: multi-step form for EU donors to save their IBAN for recurring donations.

## Acceptance Criteria
- [ ] /donate/sepa-setup page exists with multi-step flow
- [ ] Step 1: donor details (name, email)
- [ ] Step 2: IBAN entry via Stripe IbanElement + mandate authorization text
- [ ] Step 3: success/error confirmation
- [ ] Mandate authorization text displayed (legally required for SEPA)
- [ ] Integrate with POST /donations/sepa/setup-intent backend endpoint
- [ ] Link from /donate page to SEPA setup page

## Complexity Assessment
**Track**: Complex — Fullstack, Stripe Elements integration, multi-step form

## Approach
1. Create frontend/src/app/donate/sepa-setup/page.tsx (Next.js page)
2. Create SepaSetupFlow.tsx (client component with 3 steps)
3. Add link from donate page EU section to SEPA setup
