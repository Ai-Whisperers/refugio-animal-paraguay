---
task_id: T03
task_title: Implement SEPA Direct Debit Payment Method
task_status: pending
story_id: S01
epic_id: EPIC-3
created_date: 2026-03-25
estimated_effort: 8
dependencies:
  - T01-setup-stripe-api
  - T02-implement-payment-intent-webhook
  - EPIC-10 authentication for storing payment methods
---

## Overview

This task extends the Stripe integration to support SEPA Direct Debit, which allows European donors to authorize recurring donations directly from their bank accounts. Unlike credit cards, SEPA Direct Debit has lower processing fees (0.5% vs 2.9%) making it ideal for cost-effective fundraising from the European donor base. The task includes creating setup intents to securely store SEPA mandate information, validating IBAN numbers, and handling the mandate lifecycle.

## Why This Task Matters

The shelter's primary supporter base is European. SEPA Direct Debit provides several advantages: lower per-transaction fees (reducing overhead), recurring authorization support (donors can set up monthly donations once and forget), and legal compliance with EU payment regulations. European donors are familiar with SEPA and trust it as a legitimate payment method. Without SEPA support, the shelter loses access to a significant cost-efficient funding source and frustrates European supporters who expect this payment option.

## Technical Requirements

The integration must use Stripe's setup intents API to securely collect and store SEPA mandate information. A setup intent is analogous to a payment intent but used for charging future recurring payments rather than immediate one-time payments. Each setup intent results in a setup token that can be used to charge the donor's SEPA account in future transactions.

IBAN validation must occur before submission to Stripe. The application must validate that the provided IBAN has the correct length and checksum for the country (Germany: 22 characters, Spain: 24 characters, France: 27 characters, etc.). The validation happens in the request model using Pydantic validators.

The payment method storage must record the masked IBAN (last 4 digits visible, remainder masked) in the PostgreSQL payments table for UI display purposes. The full payment method ID returned by Stripe must also be stored to enable future charging without requiring the donor to re-enter their bank account.

Donors must explicitly consent to the SEPA mandate before submission. The mandate states the amount to be debited, frequency, and date of first debit. If a mandate is revoked by the donor at their bank, the next charge attempt will fail and the application must handle this gracefully by marking the mandate as revoked and alerting the admin user.

## Implementation Approach

Create a SEPA module within the Stripe integration layer that provides functions for IBAN validation, setup intent creation, and mandate confirmation. The IBAN validator uses a library or custom regex pattern to verify format and country-specific length rules.

Expose a POST endpoint at /api/donations/setup-sepa-mandate that accepts the donor's IBAN, name, and donation frequency (one-time or monthly). The endpoint creates a Stripe setup intent with the sepa_debit payment method type and returns a client_secret for the frontend to confirm payment method details.

Create a separate endpoint POST /api/donations/confirm-sepa-mandate that accepts the setup intent ID and confirms the mandate, storing the payment method ID in the database. Future one-time or recurring charges use this stored payment method.

Write pytest tests that validate IBAN formats from multiple countries, verify setup intent creation with Stripe's test API, and confirm that revoked mandates are detected on charge attempts.

## Success Criteria

POST /api/donations/setup-sepa-mandate accepts valid IBANs from France, Germany, Spain, and other EU countries and rejects invalid IBANs with clear error messages. The endpoint creates a Stripe setup intent and returns a client_secret within 500 milliseconds. POST /api/donations/confirm-sepa-mandate successfully stores the payment method ID and returns a confirmation with the masked IBAN. Future charges using the stored payment method succeed within Stripe without requiring the donor to re-enter credentials. All pytest tests pass covering IBAN validation for 10 countries and setup intent creation scenarios.

