---
story: S03
epic: EPIC-3
title: Tigo Money Integration
status: ready
created: 2026-03-25T17:13:26.729337
version: V3
---

# S03: Tigo Money Integration

## Description

Integrate Tigo Money (local Paraguayan payment provider) for accepting PYG donations from local donors without international payment friction.

## Acceptance Criteria

**Given** a local Paraguay donor wants to donate in PYG
**When** they view donation page
**Then** they see Tigo Money as payment option, marked as "Local Payment Method"

**Given** a donor selects Tigo Money
**When** they enter donation amount in PYG
**Then** they are redirected to Tigo Money checkout, see amount in PYG, and can complete payment via phone/wallet

**Given** a Tigo Money payment is completed
**When** webhook notification is received
**Then** donation record is created with PYG amount, Tigo transaction ID is stored, and confirmation email sent to donor

**Given** a donor's Tigo payment fails
**When** Tigo returns error
**Then** user sees error message with option to retry or select alternative payment method

**Given** Tigo Money transaction is processed
**When** settlement occurs
**Then** funds are received in PYG, conversion to EUR is tracked for accounting, and transaction is logged in audit trail with rate used

**Given** recurring donations via Tigo are not supported initially
**When** system configuration is reviewed
**Then** one-time donations are supported; recurring via Tigo can be deferred to future phase (manual collection or bank transfer)

## Tasks

- T01: Integrate Tigo Money API
- T02: Implement local payment flow
