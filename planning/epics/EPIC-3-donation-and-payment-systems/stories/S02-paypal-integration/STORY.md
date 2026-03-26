---
story: S02
epic: EPIC-3
title: PayPal Integration
status: ready
created: 2026-03-25T17:13:26.729079
version: V2
---

# S02: PayPal Integration

## Description

Integrate PayPal payment processing for donations with support for multiple currencies and recurring subscriptions.

## Acceptance Criteria

**Given** a donor prefers PayPal
**When** they view the donation page
**Then** they see PayPal as an available payment option alongside Stripe and other methods

**Given** a donor clicks "Pay with PayPal"
**When** they are redirected to PayPal
**Then** they authenticate, review donation amount, and confirm payment

**Given** a PayPal payment is completed
**When** PayPal redirects back to our site
**Then** a donation record is created, and donor receives confirmation email with donation details

**Given** a donor selects recurring PayPal donation
**When** they set up subscription in PayPal
**Then** we establish a billing agreement, subscription status is tracked, and cancellation is possible through account settings

**Given** a PayPal webhook is received
**When** payment.completed or subscription.created events arrive
**Then** our system processes the event, updates donation status, sends notifications, and logs transaction

**Given** currency is selected for donation
**When** PayPal processes the payment
**Then** donor sees amount in their preferred currency, and our system records both transaction currency and converted to base currency (EUR)

## Tasks

- T01: Setup PayPal SDK
- T02: Create PayPal checkout
