---
epic: EPIC-3
title: Donation & Payment Systems
status: ready
created: 2026-03-25T17:13:26.728632
updated: 2026-03-25T17:13:26.728634
---

# EPIC-3: Donation & Payment Systems

## Overview

**Goal**: Enable the shelter to accept financial donations from both European (EUR) and Paraguayan (PYG) donors through secure, auditable payment channels.

**Why it matters**: Refugio Animal Paraguay depends on donations to fund operations, veterinary care, and animal welfare programs. The owner's Dutch background and European donor network mean that EUR-denominated donations via SEPA-compatible payment methods are critical from day one. Local PYG donations are operationally important for community engagement and in-person fundraising events.

**Target users**: International donors (primarily EU/Netherlands), local Paraguayan donors, and shelter administrators who review and report on donation activity.

---

## Scope

### In Scope

- Stripe integration for credit and debit card payments from international donors in EUR
- SEPA Direct Debit via Stripe for EU bank account-based recurring donations
- Recurring subscription donations managed through Stripe's subscription billing
- Tigo Money integration for local PYG mobile wallet payments (subject to scope confirmation — see Risks)
- Webhook handling for all Stripe payment events to ensure reliable donation recording
- Donation tracking: recording donor identity, amount, currency, payment method, and timestamp
- Idempotency handling to prevent duplicate donation records from webhook retries
- A donation management dashboard for staff to view, filter, and export donation history
- EUR to PYG display conversion for operational reporting (not transactional conversion)

### Out of Scope

- PayPal integration (not in the confirmed technology stack)
- Cryptocurrency payments
- Physical check or wire transfer processing
- Real-time currency conversion between EUR and PYG for transactional purposes
- Donor-facing tax receipt generation (tracked as a future enhancement)
- Automated bank reconciliation

---

## Stories

- **S01: Stripe Integration** — Set up the Stripe SDK, configure webhook handling for `payment_intent.succeeded` and related events, implement the donation creation flow for one-time EUR card payments, and store payment records with full audit fields.

- **S02: SEPA Direct Debit and Recurring Donations** — Implement SEPA Direct Debit as a payment method for EU bank account holders using Stripe's native SEPA support. Enable recurring donation subscriptions so donors can set up monthly or annual giving. Manage subscription lifecycle events including creation, renewal, failure, and cancellation.

- **S03: Tigo Money Integration** — Integrate the Tigo Money payment API for local PYG mobile wallet donations. This story is pending confirmation of API access and scope with the Tigo Money partnership team. The integration must handle PYG amounts, mobile number-based donor identification, and Tigo Money webhook events.

- **S04: Donation Dashboard** — Build the staff-facing donation management interface backed by FastAPI endpoints. Provide paginated, filterable views of donation history, summary statistics by period and currency, and CSV export for reporting and reconciliation.

---

## Dependencies

- **Depends on EPIC-10 (Authentication & User Accounts)**: The donation dashboard requires authenticated admin/staff users. Donor accounts (optional for one-time donations, required for recurring) depend on the user registration flow.
- **Depends on EPIC-0 (Foundation)**: Database schema, Alembic migration tooling, and FastAPI application skeleton must be in place before payment routes can be added.
- **Stripe account**: A Stripe account configured for EUR/SEPA payments and webhooks is required before S01 and S02 can be tested end-to-end.
- **Tigo Money partnership**: Tigo Money API credentials and sandbox access are required before S03 can begin development. This dependency introduces scope risk.

---

## Success Metrics

- A donor based in the Netherlands can complete a one-time EUR card donation from start to confirmation in under two minutes.
- A recurring SEPA Direct Debit subscription can be set up and the first payment processed without manual intervention.
- Zero duplicate donation records exist in the database as a result of Stripe webhook retries.
- Staff can filter donation history by date range and export results as CSV within five seconds for datasets up to ten thousand records.
- Stripe webhook events are processed within five seconds of receipt in 99% of cases under normal load.

---

## Risk Factors

- **Tigo Money API availability**: If Tigo Money does not provide sandbox access or a stable API contract, S03 may need to be deferred or replaced with an alternative local payment method. The Stripe and SEPA stories (S01, S02) are not blocked by this risk.
- **SEPA mandate requirements**: SEPA Direct Debit requires collecting a signed mandate from the donor. The mandate collection flow must comply with SEPA Core Direct Debit Scheme rules, which may require legal review. Stripe handles mandate storage, but the donor-facing collection UI must be designed carefully.
- **GDPR compliance for EU donors**: Storing payment data for EU donors triggers GDPR obligations. Donation records must not store full card numbers or bank account details — Stripe handles this by providing only tokenized references. Audit logs must not include PII beyond what is necessary. Coordinate with EPIC-5 (Compliance) if it exists, or document GDPR handling decisions as part of this epic.
- **Currency handling complexity**: Stripe processes EUR amounts as integer cents. PYG does not use sub-units (it has no equivalent of cents). The data model must handle both conventions correctly and the code must never mix them.
- **Webhook replay attacks**: Stripe signs all webhook payloads. The implementation must validate the Stripe signature on every incoming webhook and reject unsigned or incorrectly signed requests.

---

## Technical Notes

Stripe's SDK for Python handles the payment intent creation, SEPA payment method attachment, subscription creation, and webhook signature verification. All Stripe API keys are loaded from environment variables and never committed to the codebase. The webhook endpoint is unauthenticated at the HTTP level (Stripe does not send JWT tokens) but is secured by signature verification.

Donation records in the database include the Stripe payment intent ID or subscription ID as a unique key to support idempotency checks. Before inserting a new donation record, the service checks whether a record with the same Stripe ID already exists. If it does, the webhook is acknowledged without creating a duplicate.

PYG amounts from Tigo Money are stored as integers in the database with the currency column set to `PYG`. EUR amounts are stored as integers representing euro-cents with the currency column set to `EUR`. Display formatting of both currencies is handled at the presentation layer, not in the database or business logic.
