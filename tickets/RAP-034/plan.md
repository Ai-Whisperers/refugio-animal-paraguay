# RAP-034 Plan

## Objective
Implement Stripe webhook processing to handle payment lifecycle events (success, failure, refund) and update donation records accordingly.

## Description
The Stripe foundation (RAP-009) created PaymentIntent support and donation models with status tracking. This ticket adds the webhook endpoint that Stripe calls when payment events occur, completing the payment lifecycle. Webhook signature verification ensures security, and the event bus integration triggers downstream notifications.

## Acceptance Criteria
- [x] POST /webhooks/stripe endpoint receives Stripe webhook events
- [x] Webhook signature verification using STRIPE_WEBHOOK_SECRET
- [x] payment_intent.succeeded updates donation status to "completed"
- [x] payment_intent.payment_failed updates donation status to "failed"
- [x] charge.refunded updates donation status to "refunded"
- [x] DonationReceived domain event published on successful payment
- [x] Idempotent processing (duplicate events return 200 without re-processing)
- [x] Proper error responses for invalid signatures (400) and unknown events (200 with skip)
- [x] Unit tests for webhook handler logic
- [x] Integration tests for the webhook endpoint
- [x] STRIPE_WEBHOOK_SECRET added to Settings config

## Complexity Assessment
**Track**: Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [x] Single, clear root cause identified
- [ ] Solution affects <=3 files — NO, affects 5+ files
- [ ] Change impact <=10 lines of actual code — NO, ~150+ lines
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — multiple files (new router, config update, app registration, tests), webhook signature verification, event bus integration, and idempotency handling.

## Approach
1. Add STRIPE_WEBHOOK_SECRET to Settings config
2. Create src/api/webhooks.py with POST /webhooks/stripe endpoint
3. Implement signature verification via stripe.Webhook.construct_event
4. Create handler functions for each event type (succeeded, failed, refunded)
5. Integrate with event bus (publish DonationReceived on success)
6. Register webhook router in app.py
7. Write unit tests for handler logic and integration tests for endpoint

## Dependencies
- Depends on: RAP-009 (Stripe Foundation) — DONE
- Depends on: V2 #1 Event Bus Infrastructure — DONE (PR #14)
- Depends on: V2 #12 Email Notification System — DONE (PR #18)

## Risks
- Risk: Stripe SDK version changes webhook API → Mitigation: Pin stripe>=8.0, test with mock events
- Risk: Race condition on duplicate webhook delivery → Mitigation: Check donation status before update, idempotent design
