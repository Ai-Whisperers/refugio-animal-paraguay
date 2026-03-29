# RAP-203 Plan

## Objective
Send WhatsApp donation receipt via Meta Cloud API when a donation payment is confirmed, so donors receive an instant confirmation on WhatsApp.

## Acceptance Criteria
- [ ] `phone` column added to `donors` table (migration 082)
- [ ] `Donor` ORM model has `phone` field
- [ ] `MetaWhatsAppDonationHandler` subscribes to `DONATION_RECEIVED` events
- [ ] Handler looks up donor phone, name, amount, currency, receipt from donation_id
- [ ] Handler sends `donation_receipt` template via `MetaWhatsAppService`
- [ ] Handler skips silently when donor has no phone or Meta disabled
- [ ] 11 unit tests covering all cases
- [ ] Handler wired in app.py

## Complexity Assessment
**Track**: Simple — adds phone field to donor, creates handler, no breaking changes

## Approach
1. Migration 082: add phone to donors
2. Update Donor ORM model
3. Create MetaWhatsAppDonationHandler
4. Wire in app.py
5. Write unit tests

## Dependencies
- RAP-200: MetaWhatsAppService (done)
- RAP-201: Template registry (done)
