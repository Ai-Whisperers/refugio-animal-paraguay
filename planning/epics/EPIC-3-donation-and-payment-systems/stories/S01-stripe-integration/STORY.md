---
story: S01
epic: EPIC-3
title: Stripe Integration
status: ready
created: 2026-03-25T17:13:26.728764
version: V2
---

# S01: Stripe Integration

## Description

Integrate Stripe payment processing for EUR/USD donations with SEPA support for EU donors and automatic tax receipt generation.

## Acceptance Criteria

**Given** a donor wants to make a one-time donation
**When** they visit the donation page
**Then** they see a Stripe payment form accepting card, SEPA, and other payment methods

**Given** a donor enters payment details
**When** they submit the donation form
**Then** Stripe processes the payment securely, returns a confirmation token, and no payment credentials are stored in our database

**Given** a donation is EUR amount
**When** the payment is processed
**Then** Stripe handles currency conversion if needed, charges are in EUR for EU donors, and receipt shows EUR amount

**Given** a payment is successful
**When** the transaction completes
**Then** a donation record is created with: amount, currency, donor info, payment method, transaction ID, timestamp, and tax receipt flag

**Given** a payment fails
**When** Stripe rejects the transaction
**Then** user receives error message with reason (insufficient funds, incorrect details, etc.) and can retry

**Given** a donor wants recurring donations
**When** they select monthly/yearly donation option
**Then** Stripe creates a subscription, charges are recurring on schedule, and donor receives reminder emails before each charge

**Given** a webhook from Stripe arrives
**When** a payment.success or charge.failed event occurs
**Then** our system updates donation status, sends confirmation/failure emails, and logs the transaction for accounting

## Tasks

- T01: Setup Stripe API
- T02: Create payment form
- T03: Handle webhooks
