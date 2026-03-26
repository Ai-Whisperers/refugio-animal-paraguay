---
task_id: T01
task_title: Setup Stripe API Integration
task_status: pending
story_id: S01
epic_id: EPIC-3
created_date: 2026-03-25
estimated_effort: 6
dependencies:
  - donations table in PostgreSQL
  - EPIC-10 authentication (JWT for authenticated donor endpoints)
  - Stripe account configured for EUR/SEPA
---

## Overview

This task establishes the foundational Stripe integration layer for the application. It covers installing and configuring the Stripe Python SDK, implementing the payment intent creation endpoint, storing the Stripe publishable key in application configuration, wiring the STRIPE_SECRET_KEY from environment variables into the Stripe SDK, and verifying connectivity to Stripe's test API. This is the prerequisite for all payment processing tasks in EPIC-3.

## Why This Task Matters

Donations in EUR from European supporters are the primary recurring funding source for the shelter. Stripe is selected because it provides native SEPA Direct Debit support for European bank accounts, has robust webhook infrastructure for asynchronous payment confirmation, and is the leading payment processor for European non-profits receiving international donations. Without this foundational integration, the entire donation system cannot operate.

## Technical Requirements

The Stripe Python SDK must be version 8.x or later, supporting asynchronous HTTP operations. The STRIPE_SECRET_KEY environment variable must be read during application startup and injected into the Stripe client. The Stripe publishable key (a non-sensitive identifier) must be stored in the application configuration and returned to frontend requests so the Stripe Elements JavaScript library can be initialized on the donation form.

All Stripe API calls must default to EUR currency and record currency denomination in euro-cents (smallest unit). The integration must support payment intents with metadata fields to track shelter_id, campaign_id, and donor_user_id (if authenticated). Webhook endpoints will be configured in a subsequent task but the SDK foundation must support them.

Error handling must distinguish between network failures (retryable), validation errors (4xx responses from Stripe), and Stripe service errors (5xx). The application must never expose Stripe's error codes directly to the frontend; instead, it must return generic error messages ("Payment processing failed. Please contact support.") while logging the full Stripe error for debugging.

## Implementation Approach

Begin by adding the Stripe Python package to the project dependencies. Create a new module that initializes the Stripe client with the secret key retrieved from environment variables during application startup. This module must export a function that creates a payment intent with the given amount in euro-cents, currency code (EUR), and metadata dictionary.

The FastAPI application must expose a POST endpoint at /api/donations/create-payment-intent that accepts a JSON request containing donation_amount_cents, campaign_id (optional), and donor_user_id (optional if authenticated). This endpoint uses dependency injection to verify the request is valid and authenticated if required.

The endpoint calls the Stripe integration module to create a payment intent, captures the client_secret from the response, and returns a JSON response containing the client_secret, amount in euro-cents, and currency code. The response does not include the Stripe publishable key; instead, a separate GET endpoint /api/config/stripe-key returns only the publishable key for frontend initialization.

Write pytest tests that mock the Stripe SDK to verify the payment intent creation returns the correct structure and that error cases are handled gracefully without exposing sensitive information.

## Success Criteria

The Stripe SDK is installed and the application starts successfully with a valid STRIPE_SECRET_KEY in the environment. The POST /api/donations/create-payment-intent endpoint accepts valid donation requests and returns a client_secret within 500 milliseconds. The GET /api/config/stripe-key endpoint returns the publishable key without requiring authentication. Error responses do not expose Stripe error codes or API details. All pytest tests pass with 100% coverage of the Stripe integration module. The integration successfully creates a test payment intent in Stripe's test environment when called with valid parameters.

