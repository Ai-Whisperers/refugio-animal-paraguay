# RAP-151 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-27

## Current Focus
Frontend SEPA mandate creation flow implemented.

## Technical State
- /donate/sepa-setup page created
- SepaSetupFlow component with 3 steps: donor details, IBAN, confirmation
- Uses Stripe IbanElement for IBAN collection
- Mandate authorization text in Spanish (legally required)
- Links from /donate page EU section
