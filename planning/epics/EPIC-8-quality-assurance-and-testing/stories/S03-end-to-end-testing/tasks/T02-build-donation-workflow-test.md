---
task: T02
story: S03
epic: EPIC-8
title: Build donation workflow test
status: ready
priority: medium
created: 2026-03-25T17:13:26.735623
---

# T02: Build donation workflow test

## Description

Build the end-to-end test that exercises the complete EUR donation lifecycle from payment intent creation through Stripe webhook processing to the final completed donation record and notification. A second variant covers the PYG cash donation path. Both tests run against the real FastAPI application with a real PostgreSQL test database.

## What the EUR Donation Test Covers

The EUR donation workflow test has six sequential stages. Stripe is exercised in test mode using Stripe's test API keys. No real charges are created.

## Stage One: Payment Intent Creation

The test calls the donation creation endpoint with a POST request containing a EUR amount in cents, a currency code of EUR, an optional donor name, and an optional message. The endpoint is public and requires no authentication, reflecting the design that anonymous donors can contribute without creating an account.

The expected response status is 201 Created. The response body must contain a Stripe payment intent client secret, a donation record ID, and a donation status of pending. The test saves both the client secret and the donation record ID for subsequent stages.

The test also queries the database directly and asserts that a donation record exists with the status pending, the correct amount in cents, and no completed timestamp.

## Stage Two: Pending State Verification

The test calls the donation status endpoint with the donation record ID. This is a public read endpoint. The expected response contains the donation with status pending and a created timestamp. The test asserts that the amount and currency in the response match what was submitted in stage one.

This stage verifies the read path works independently of the write and webhook paths.

## Stage Three: Stripe Webhook Simulation

The test constructs a Stripe webhook event payload of type `payment_intent.succeeded`. The payload contains the payment intent ID returned from Stripe in stage one, an amount matching the donation amount, a currency of EUR, and metadata containing the internal donation record ID.

The test computes a valid Stripe webhook signature using the test webhook signing secret. This is the same signature verification logic that the application's webhook endpoint uses. Constructing a correctly signed payload without the actual Stripe infrastructure is straightforward using the Stripe test SDK's webhook construction utility.

The test posts this payload to the webhook endpoint with the signature in the header. The expected response is a 200 OK with a simple acknowledgment body. The endpoint must respond within two seconds to satisfy Stripe's webhook delivery expectations.

## Stage Four: Completed Record Verification

The test queries the donation status endpoint again for the same donation record ID. The expected response now shows the donation with status completed, a non-null completed timestamp, and the same amount and currency as stage one.

The test also queries the database directly to confirm that the donation row's status and completed timestamp were updated correctly and that no duplicate donation record was created.

## Stage Five: Notification Record

The test queries the notification log. For a EUR donation with a donor email address provided in stage one, a notification record should exist in the notification log referencing the donation record ID and indicating the notification type as donation confirmation.

This stage does not verify that an email was actually sent, since transactional email delivery happens asynchronously and involves an external service. It verifies only that the notification dispatch was triggered and recorded.

## Stage Six: Idempotency Check

The test resends the same Stripe webhook payload from stage three — the same payment intent ID and donation record ID — to the webhook endpoint. This simulates Stripe's at-least-once delivery guarantee, where the same event may be delivered more than once.

The expected response is again 200 OK. The test then queries the database and asserts that the donation record still shows a single completed entry and that no duplicate donation record was created. The idempotency key in the donation record (the Stripe payment intent ID) must prevent a second completion from creating duplicate state.

## PYG Cash Donation Variant

The PYG cash donation test covers a simpler two-stage flow, since cash donations do not involve Stripe.

The test calls the donation creation endpoint with a PYG amount as an integer (no sub-unit), a currency code of PYG, a payment method of cash, and a donor contact method. The expected response is 201 Created with a donation record of status pending and no payment intent client secret since no Stripe payment is involved.

The test then simulates a staff member manually marking the donation as received by calling the staff-only donation confirm endpoint with the staff JWT token. The expected response shows the donation with status completed and the staff member's ID recorded as the confirming user.

A database-level assertion verifies that the cash donation record's amount is stored as a whole-number integer (never a decimal or floating-point value) and that the currency field is PYG.

## Test Setup and Teardown

The test uses a pytest fixture that provides a set of valid test Stripe API credentials loaded from test environment variables. The fixture fails fast with a clear error if these variables are not set, since Stripe test mode requires real (though non-charged) API keys. A separate fixture provides test webhook secrets for signature computation.

All donation records created during the test are inserted within a transaction that is rolled back after the test completes. Stripe payment intents created in test mode are automatically cleaned up by Stripe after a short period and do not require explicit teardown from the test.
