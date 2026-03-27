# RAP-074 Plan

## Objective
Integrate Tigo Money (Paraguayan mobile wallet) as a PYG payment method for local donors.

## Description
Tigo Money is Paraguay's dominant mobile wallet, used by millions for daily transactions. Local donors prefer it over credit cards. This story adds Tigo Money as a payment option alongside Stripe: a service layer wraps the Tigo API (HTTP redirect + webhook pattern), a new API endpoint initiates checkout and handles callbacks, and donation records are created on payment confirmation.

## Acceptance Criteria
- [ ] PaymentMethod enum includes TIGO_MONEY value
- [ ] Settings has tigo_money_enabled, tigo_merchant_id, tigo_api_key, tigo_webhook_secret fields
- [ ] TigoMoneyService wraps the Tigo HTTP API; fails gracefully when disabled
- [ ] POST /tigo-money/initiate — creates pending donation, returns Tigo checkout URL
- [ ] POST /tigo-money/callback — webhook handler: verifies signature, updates donation status, emits DONATION_RECEIVED event
- [ ] Donation schema updated to accept tigo_money as payment_method
- [ ] Migration adds tigo_money to the CHECK constraint on donations.payment_method
- [ ] Unit tests: service (enabled/disabled, initiate, callback), endpoint schemas
- [ ] No real Tigo credentials committed

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — new service, new API router, DB migration, schema changes, event emission.

## Approach
1. Add TIGO_MONEY to PaymentMethod enum + migration to update DB CHECK constraint
2. Extend Settings with Tigo Money config fields
3. Create TigoMoneyService (src/services/tigo_money_service.py)
4. Create tigo_money API router (src/api/tigo_money.py)
5. Register router in app.py
6. Update donation schemas
7. Write unit tests

## Dependencies
- Depends on: Stripe foundation (DONE), donation model (DONE), event bus (DONE)
- Blocked by: None
