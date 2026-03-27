---
story: S3
epic: EPIC-77
ticket: RAP-509
title: "Voucher purchase flow for donors"
status: ready
points: 8
priority: P0
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S3: Voucher purchase flow for donors

## Story
As a **donor**, I want **to purchase veterinary service vouchers** so that **I can directly support animal medical care at specific clinics**.

## Description
Create complete voucher purchase flow where donors select clinic, service type, quantity, and pay via Stripe or SEPA. Vouchers are created and stored in donor's wallet.

## Acceptance Criteria
- [ ] /donate/voucher page accessible to logged-in donors, shows: clinic selector dropdown (list all active clinics), service type selector (populated from selected clinic's services), quantity input (1-100, default 1), price display (calculated as service price * quantity)
- [ ] Clinic selector: GET /api/clinics/active returns list of active clinics with basic info (id, name, address)
- [ ] Service type selector: GET /api/clinics/{clinic_id}/services returns services for selected clinic
- [ ] Price calculator: real-time shows total: quantity * service_price, formatted with currency
- [ ] Payment integration: "Pay with Stripe" button OR "Pay with SEPA" button (mutually exclusive)
- [ ] Stripe payment: redirect to Stripe checkout with: amount (total price in cents), currency (clinic's currency), description ("Veterinary Voucher - [service type] at [clinic name]"), success_url, cancel_url
- [ ] SEPA payment: show SEPA details (account holder, IBAN, BIC, amount, reference) with instructions to transfer, pending receipt of payment
- [ ] POST /api/donations/voucher endpoint: creates donation record with type='voucher', target_id=clinic_id, amount_cents=total, payment_method='stripe'|'sepa', status='pending_payment', returns payment_intent_id or sepa_reference
- [ ] After successful Stripe payment (webhook from Stripe): create VetVoucher records for each voucher purchased
- [ ] After SEPA payment received (manual verification): admin marks donation as confirmed, creates VetVouchers
- [ ] VetVoucher creation: create N vouchers (qty=1 each) with: code=UUID, donor_id=current_user_id, clinic_id, service_id, status='purchased', amount_cents=service_price, purchased_at=now()
- [ ] After voucher creation: send confirmation email to donor with: donation summary, list of voucher codes (or downloadable PDF with QR codes), instructions for sharing with rescuers
- [ ] Donor can view vouchers in /portal/vouchers page: list of purchased vouchers, status, clinic name, service type, amount
- [ ] Voucher expiry: set expires_at = purchased_at + 90 days
- [ ] Form validation: clinic required, service required, quantity 1-100
- [ ] Error handling: payment failure shows error message, allows retry
- [ ] Confirmation page after payment: shows success message, voucher list, share buttons

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test voucher creation, price calculation, payment status handling
- [ ] Integration test: purchase single voucher with Stripe
- [ ] Integration test: purchase multiple vouchers (quantity > 1)
- [ ] Integration test: Stripe webhook creates vouchers correctly
- [ ] Integration test: SEPA payment flow creates donation in pending state
- [ ] Integration test: email sent to donor after purchase
- [ ] Component test: responsive UI on mobile/tablet/desktop
- [ ] Integration test: vouchers appear in donor's wallet
- [ ] Manual testing: Stripe test payments processed correctly
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/donate/voucher.tsx with form, Stripe integration
- Backend: FastAPI endpoint POST /api/donations/voucher, Stripe webhook handler at /webhooks/stripe
- Stripe integration: use Stripe Python client, create PaymentIntent, handle webhook events (payment_intent.succeeded)
- SEPA payment: generate reference code, show static SEPA details, require manual admin verification
- VetVoucher creation: transaction ensures all vouchers created atomically
- Email: send via Mailgun/SendGrid with voucher PDF attachment (generated via reportlab or similar)
- QR codes: encode voucher code in QR format, include in email and PDF
- Voucher PDF: one page per voucher with logo, code, QR code, clinic name, service, expiry date
- Currency handling: use clinic's currency for pricing and payment
- Donation record: tracks high-level donation, VetVouchers track individual vouchers

## Story Points: 8
