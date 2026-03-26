# RAP-025 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Implementing cash donation recording endpoint.

## Technical State
- Donation model already supports PaymentMethod.CASH
- Existing `POST /donations` creates donations with pending status (designed for Stripe flow)
- Need separate endpoint for cash that creates with completed status immediately

## Next Steps
1. Add receipt_number to Donation model + migration
2. Create CashDonationCreate schema
3. Add POST /donations/cash endpoint
4. Write tests

## Blockers
- None

## Key Decisions Made
- Separate endpoint rather than overloading existing create_donation (cleaner API, different auth requirements)
