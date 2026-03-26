---
task: T01
story: S01
epic: EPIC-8
title: Write API tests
status: ready
priority: medium
created: 2026-03-25T17:13:26.735001
---

# T01: Write API tests

## Description

Create the integration test suite that covers every FastAPI route in the application. These tests exercise the full request-response cycle against a real PostgreSQL test database, verifying that endpoints behave correctly across all supported roles, input variations, and error conditions.

## Approach

The test suite lives under the `tests/integration/` directory. Each module under `tests/integration/` corresponds to a router module in the application: adoption routes have their own test file, donation routes have their own, animal management routes have their own, and so on.

The test runner is pytest. HTTP requests are issued through `httpx.AsyncClient` with the FastAPI application mounted as the ASGI transport. This means every test makes real HTTP calls through the full middleware stack — authentication, validation, dependency injection, and database access — without starting an actual server process. Tests are therefore fast and self-contained.

## Test Database Setup

A dedicated PostgreSQL test database is used during the test run. A conftest.py fixture at the top of the tests directory handles setup and teardown. Before the test session begins, the fixture runs all Alembic migrations against the test database to bring it to the current schema. After the session ends, the fixture drops and recreates the test database, leaving it clean for the next run.

Each individual test receives a database session that is wrapped in a transaction. The transaction is rolled back at the end of the test rather than committed, so every test starts with a clean slate regardless of what previous tests inserted. This transactional isolation strategy means tests can run in any order and there is no shared mutable state between them.

The test database URL is read from an environment variable, never hardcoded. The CI environment sets this variable via a PostgreSQL service container defined in the GitHub Actions workflow.

## JWT Authentication Fixtures

A conftest.py fixture generates JWT tokens for each role in the system. The fixtures are named `admin_token`, `staff_token`, and `adopter_token`. Each fixture returns a signed JWT string that can be passed as a bearer token in the Authorization header.

Tokens are generated using the same signing key and expiry logic used by the application itself, loaded from test environment variables. This means the application's own authentication middleware validates these tokens without any special test-mode bypass.

Tests that require authentication pass the token in the request headers. Tests that verify authentication enforcement make the same request without a token and assert a 401 Unauthorized response, and then make it with an insufficient-privilege token and assert a 403 Forbidden response.

## What Each Test Covers

For every route, the test file includes at minimum the following scenarios:

The happy path test sends a well-formed request with the appropriate role and asserts the expected HTTP status code, the response body structure matching the Pydantic response schema, and any expected side effects such as a new database record or a changed status field.

The authentication tests verify that unauthenticated requests receive a 401 response and that requests authenticated with an insufficient role receive a 403 response.

The validation error tests send requests with missing required fields, fields of the wrong type, and fields that violate domain constraints such as negative donation amounts or empty animal names. Each of these should return a 422 Unprocessable Entity response. The response body should follow FastAPI's standard validation error format, with the detail array identifying which fields failed and why.

The not-found tests verify that requests referencing non-existent resource IDs return 404 responses with a structured error body.

The conflict tests cover scenarios where uniqueness constraints are violated, such as submitting a second adoption request for the same animal by the same adopter. These should return 409 Conflict responses.

## Specific Route Coverage

The adoption routes tests cover submitting a new adoption request, listing all requests for the authenticated adopter, retrieving a single request by ID, and the staff-only routes for reviewing and approving or rejecting a request. The status transition from pending to approved or rejected must be verified at the database level by querying the record after the API call.

The donation routes tests cover creating a payment intent, retrieving a donation record after webhook processing, and listing donations filtered by status and date range. The Stripe webhook handler is tested by sending a fake webhook payload with a valid signature computed using the test webhook secret.

The animal routes tests cover public read endpoints that return without authentication, staff-only write endpoints for creating and updating animal records, and the search endpoint with filtering by species, status, and age range.

The admin routes tests use the admin token exclusively and verify that staff tokens receive 403 responses, confirming that the role hierarchy is enforced at the route level.

## Coverage Target

The integration test suite for API routes must achieve at least ninety percent line coverage across all router modules. Any gap below this threshold must be resolved before the story is considered complete. The coverage report is generated by running pytest with the coverage plugin configured to measure only the application source, not the test files themselves.
