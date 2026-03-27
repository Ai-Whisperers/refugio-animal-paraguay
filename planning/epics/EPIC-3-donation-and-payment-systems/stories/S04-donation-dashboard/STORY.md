---
story: S04
epic: EPIC-3
title: Donation Dashboard
status: done
ticket: RAP-037
pr: 56
created: 2026-03-25T17:13:26.729593
version: V2
---

# S04: Donation Dashboard

## Description

Donor-facing dashboard showing donation history, receipts, impact metrics, and subscription management with ability to download records.

## Acceptance Criteria

**Given** a donor logs into their account
**When** they navigate to Donations or Dashboard
**Then** they see a personal donation dashboard with total donated, donation count, and recent donations list

**Given** I view my donation history
**When** the dashboard loads
**Then** I see a table showing each donation: date, amount, currency, payment method, status (completed/refunded), and action buttons

**Given** a donation was made
**When** I view donation details
**Then** I can see: exact amount, currency, conversion rate (if applicable), payment method, transaction date, and receipt link

**Given** I have a completed donation
**When** I click "Download Receipt"
**Then** a tax-deductible receipt PDF is generated with shelter info, donation amount, date, and tax ID (if applicable)

**Given** I have active recurring donations
**When** I view subscriptions section
**Then** I see active subscriptions with amount, frequency (monthly/yearly), next billing date, and option to pause/cancel

**Given** I want to update payment method for recurring donation
**When** I click "Update Payment Method"
**Then** I can change card, PayPal, or other payment method and confirm update

**Given** donations are tracked over time
**When** I view dashboard
**Then** I see impact summary: "Your donations have helped X animals receive Y hours of care" (or similar personalized metric)

## Tasks

- T01: Create donation history view
- T02: Implement analytics dashboard
