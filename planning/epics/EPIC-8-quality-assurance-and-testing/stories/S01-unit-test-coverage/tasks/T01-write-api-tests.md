---
task_id: T01
task_title: "Write API Endpoint Tests Using FastAPI TestClient"
task_status: pending
story_id: S01
epic_id: EPIC-8
created_date: 2026-03-25
estimated_effort: 10 hours
dependencies:
  - T01-setup-stripe-api (EPIC-3-S01)
  - T02-implement-adoption-workflow (EPIC-1-S02)
  - T01-implement-donation-workflow (EPIC-3-S02)
---

## Overview

This task involves writing comprehensive unit tests for all FastAPI HTTP endpoints across the Refugio Animal Paraguay application. The tests must cover adoption request submission endpoints, donation creation endpoints, payment intent endpoints, and authorization-related endpoints. These tests use FastAPI's TestClient library to simulate HTTP requests against the application without requiring a running server. The test suite validates request handling, response formats, status codes, error conditions, and edge cases for each endpoint.

## Why This Task Matters

API endpoint tests form the foundation of the test pyramid by providing immediate feedback on endpoint behavior. When developers modify route handlers, parameter validation, or response schemas, these tests catch regressions immediately. FastAPI's TestClient allows testing endpoints in isolation, which means tests run quickly and do not depend on external services like payment processors or email systems. These tests also document the expected request and response formats, serving as executable specifications that keep documentation synchronized with actual implementation.

## Technical Requirements

The test suite must validate adoption request endpoints that handle POST requests to submit new adoption applications, GET requests to retrieve adoption requests by identifier, PATCH requests to update adoption request status, and DELETE requests to withdraw adoption applications. Each adoption endpoint test verifies that valid adoption data produces HTTP 201 Created responses with complete adoption records in the response body, including adoption_id, adopter_email, animal_id, status (pending), request_date, and estimated_completion_date. Tests must validate that requests with missing required fields produce HTTP 422 Unprocessable Entity responses with validation error details explaining which fields are missing.

The donation workflow endpoints require testing POST requests that submit new donations with amount_in_cents, donor_email, currency (EUR or PYG), and donation_type (one-time or recurring). Valid donation submissions must produce HTTP 201 Created responses containing donation_id, status (pending_payment), created_at, and payment_intent_id for directing donors to the Stripe payment form. Tests must verify that donation amounts less than one hundred cents (minimum one euro or PYG equivalent) produce HTTP 400 Bad Request responses with explicit error messages about minimum donation amounts.

Payment intent endpoints must handle requests that retrieve the current status of payment intents, including payment_id, status (requires_payment_method, requires_confirmation, succeeded), amount_in_cents, currency, and error_message if payment failed. Tests verify that requesting a non-existent payment intent identifier produces HTTP 404 Not Found responses. All endpoints must include test cases validating that requests without proper JWT authentication headers produce HTTP 401 Unauthorized responses, and requests with expired or malformed tokens produce HTTP 403 Forbidden responses.

Response validation tests must confirm that all endpoint responses follow Pydantic schema validation, meaning numeric values for monetary amounts use integer types representing cents, date fields use ISO 8601 format strings, and nested objects (like donor information within donation responses) include all documented fields. Tests must validate that endpoints reject requests with invalid email addresses using RFC 5322 validation rules, producing HTTP 422 Unprocessable Entity responses identifying the email_address field as invalid.

Error handling test cases must verify that database constraint violations (like foreign key violations when referencing non-existent animals) produce HTTP 409 Conflict responses with error messages identifying the constraint violation. Tests for concurrent request scenarios must confirm that race conditions do not occur when multiple adoption requests are submitted for the same animal simultaneously, ensuring that only one adoption request can proceed to status accepted while others receive HTTP 409 Conflict responses.

Status code consistency tests verify that successful resource creation operations produce HTTP 201 Created responses, successful retrievals produce HTTP 200 OK responses, successful updates produce HTTP 200 OK responses, and successful deletions produce HTTP 204 No Content responses. All error responses must include Content-Type headers specifying application/json and response bodies containing error_code, error_message, and timestamp fields for structured error handling in client applications.

## Implementation Approach

The test suite begins by creating a fixture that instantiates the FastAPI TestClient pointing to the application instance. This fixture provides a client object used throughout the test module for making simulated HTTP requests. A second fixture manages test database setup and teardown, creating a clean test database schema before each test and removing test data after each test completes. This isolation ensures tests do not interfere with each other and can run in any order.

Adoption request tests are organized into groups by endpoint. Adoption submission tests verify that valid adoption data with required fields email address, animal_id, reason_for_adoption, and household_type produces successful creation responses. Tests include variations covering different animal types (dog, cat, other), different household configurations (apartment, house, farm), and different reason_for_adoption values (family pet, working animal, emotional support). Each variation confirms the endpoint correctly processes the specific combination.

Adoption retrieval tests verify that fetching an adoption request by its identifier returns the complete adoption record with all fields populated. Tests include cases where the adoption has never been modified (only has initial created_at timestamp), cases where adoption status has been updated multiple times (testing that updated_at and status fields reflect the latest change), and cases where the adoption includes associated notes from shelter staff.

Adoption update tests verify that PATCH requests with new status values (e.g., from pending to approved) correctly modify the adoption record. Tests confirm that only authorized staff members (verified through JWT claims) can update adoption status, and attempts by non-staff users produce HTTP 403 Forbidden responses. Tests verify that adopter users cannot change their own adoption status through direct API calls.

Adoption deletion tests confirm that DELETE requests withdraw adoption applications, changing status to withdrawn and setting withdrawn_at timestamp. Tests verify that only the adopter user who submitted the application can delete their own adoption request, enforcing access control through JWT claims.

Donation submission tests validate POST requests with donation amounts in euro-cents for EUR donations (minimum one hundred euro-cents, i.e., 1.00 EUR) and amounts in PYG cents for PYG donations. Tests verify that valid donations produce payment_intent_id values ready for Stripe payment processing. Tests include edge cases like donations with very large amounts (testing for numeric overflow or Stripe limits), and donations with special characters in donor names (testing input sanitization).

Donation retrieval tests verify that GET requests fetch complete donation records including all associated metadata. Tests confirm that donors can retrieve their own donation records, and staff can retrieve any donation record. Non-authenticated requests produce HTTP 401 Unauthorized responses.

Payment intent status tests verify that GET requests to payment status endpoints return current payment processing status. Tests include cases where payment processing has not yet begun (status requires_payment_method), cases where Stripe payment processing is in progress (status requires_confirmation), and cases where payment succeeded (status succeeded with captured payment amount).

Authentication tests verify that endpoints requiring authorization reject requests without JWT headers, requests with invalid tokens, and requests with tokens that lack required role claims. Tests confirm that adoption-related endpoints can only be accessed with either adopter or staff roles, and donation endpoints can be accessed by donors or staff. Payment-related endpoints must require staff role access.

## Success Criteria

All adoption request endpoints have unit tests that achieve at least ninety-five percent code coverage for the endpoint handler functions. Tests verify both successful request paths and all documented error conditions. Test execution completes in under thirty seconds for the entire adoption endpoint test suite.

Donation workflow endpoints have unit tests covering valid submissions with both EUR and PYG currencies, invalid amount values, missing required fields, and permission enforcement. At least ninety percent of the donation endpoint handler code paths execute during testing. The test suite validates response schemas against Pydantic models and confirms all documented fields appear in responses.

Payment status endpoints have tests confirming correct status retrieval, handling of non-existent payment identifiers, and permission enforcement. Tests verify that only staff members can retrieve payment status information, and attempts by non-staff users produce appropriate authorization errors.

All error response tests confirm that HTTP status codes follow REST conventions, response bodies contain structured error information with error_code and error_message fields, and error messages are helpful for client application developers without exposing sensitive system details.

The complete API endpoint test suite can run using the pytest command on the tests/api/ directory, and all tests pass with zero failures. Test output clearly identifies any failures with the endpoint path, HTTP method, and assertion that failed. Tests can be run in parallel without conflicts using pytest-xdist plugin configuration.

