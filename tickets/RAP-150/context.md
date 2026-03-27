# RAP-150 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-27

## Current Focus
Adding SEPA SetupIntent endpoint to src/api/sepa.py and schemas.

## Technical State
- existing sepa.py has PaymentIntent creation (charge immediately)
- Stripe SetupIntent creates a mandate without charging
- Donation model has stripe_customer_id field for tracking

## Next Steps
1. Add schemas
2. Add API endpoints
3. Write tests
