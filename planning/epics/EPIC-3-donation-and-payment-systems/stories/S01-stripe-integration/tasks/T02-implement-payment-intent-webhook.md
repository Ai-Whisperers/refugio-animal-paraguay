---
task_id: T02
task_title: Implement Payment Intent Webhook Handler
task_status: pending
story_id: S01
epic_id: EPIC-3
created_date: 2026-03-25
estimated_effort: 8
dependencies:
  - T01-setup-stripe-api
  - EPIC-5 email notifications (send confirmation to donor and shelter staff)
  - donations table with stripe_payment_id column
---

## Overview

This task implements the webhook endpoint that receives payment confirmation events from Stripe when a donor completes payment. The webhook verifies the authenticity of Stripe's signature, updates the donation record in PostgreSQL with the Stripe payment intent ID and status, and triggers downstream workflows such as sending confirmation emails and updating donation campaign totals.

## Why This Task Matters

Stripe webhooks are the asynchronous backbone of donation processing. When a donor completes payment on the frontend using Stripe Elements, the payment intent transitions through multiple states (requires_payment_method, processing, succeeded, failed). Only the webhook notifications guarantee that the application learns about final payment outcome. Without webhooks, donations could succeed at Stripe but the application database would remain unaware, creating a critical gap where funds are collected but not recorded.

## Technical Requirements

The webhook endpoint must be a FastAPI route that accepts POST requests at /api/webhooks/stripe-events. Every incoming webhook must be verified using Stripe's signature verification mechanism with the STRIPE_WEBHOOK_SECRET environment variable. Stripe requires that webhook handlers respond with HTTP 200 status within 30 seconds to indicate receipt; if the handler takes longer or returns an error status, Stripe retries the webhook up to 5 times over 3 days.

The handler must parse the Stripe event JSON and extract the payment_intent object. It must record the event_id in the database to prevent duplicate processing if Stripe retries. The handler must update the donation record in PostgreSQL by matching the payment intent ID, recording the final status (succeeded or failed), timestamp of confirmation, and associated fee (if available from the Stripe response).

If the payment intent status is succeeded, the donation amount becomes immutable and the donation triggers downstream workflows. If the payment intent status is failed, the donation record must be marked as failed with the reason code from Stripe (insufficient_funds, lost_card, card_declined, etc.).

## Implementation Approach

Create a Stripe webhook secrets module that reads STRIPE_WEBHOOK_SECRET from the environment and provides a verification function that validates the raw request body and X-Stripe-Signature header. This function raises an exception if verification fails.

Create a webhook handler function that accepts the raw request body and signature header, verifies authenticity, parses the event JSON, and dispatches based on event type. For payment_intent.succeeded and payment_intent.payment_failed events, the handler calls a donation update function that inserts or updates the donation record with the Stripe payment ID and final status.

The FastAPI endpoint creates a response immediately returning HTTP 200 before processing, ensuring Stripe receives immediate acknowledgment. Then it processes the webhook in a separate task using FastAPI BackgroundTasks or a queue system so that network delays in sending confirmation emails do not cause the webhook handler to timeout.

Write pytest tests that mock Stripe webhook events with valid signatures and verify the donation record is updated correctly. Test edge cases such as duplicate webhook events (same event_id sent twice) and missing donation records (webhook for a payment intent not in our system).

## Success Criteria

The webhook endpoint is deployed at /api/webhooks/stripe-events and responds to POST requests with HTTP 200 within 1 second. Stripe's webhook signature verification rejects unsigned or tampered webhook events with HTTP 401 Unauthorized. When a payment_intent.succeeded event is received with valid signature, the donation record is updated with the Stripe payment ID and status marked as confirmed within 100 milliseconds. Duplicate webhook events (same event_id) are detected and ignored, preventing double-crediting. Downstream workflows (confirmation email, campaign total update) are triggered asynchronously without blocking the webhook response. All pytest tests pass with 100% coverage of webhook validation and database update logic.

