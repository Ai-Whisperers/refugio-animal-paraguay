---
task_id: T02
task_title: Implement API Endpoint Tests with FastAPI TestClient
task_status: pending
story_id: S01
epic_id: EPIC-8
created_date: 2026-03-25
estimated_effort: 8
dependencies:
  - T01-setup-pytest-configuration
  - All API endpoints in prior epics (EPIC-11 public endpoints, EPIC-7 admin endpoints)
---

## Overview

This task implements comprehensive endpoint tests using FastAPI's TestClient to verify that API routes accept valid requests, return correct response codes and JSON structures, reject invalid requests with appropriate error messages, and enforce authentication and authorization. Tests cover the happy path (valid input produces expected output) and sad paths (invalid input, missing data, permission denied).

## Why This Task Matters

API endpoints are the primary interface to the application. If an endpoint behaves incorrectly, user-facing functionality breaks. Without endpoint tests, bugs in request parsing, validation, authentication, and response formatting are discovered by users in production rather than developers in testing. Endpoint tests catch regressions early when code is changed.

## Technical Requirements

Tests must use FastAPI's TestClient to make actual HTTP requests to the application without requiring a running server. The TestClient automatically handles request serialization and response deserialization.

Each endpoint must have tests covering at least these scenarios: valid request with all required fields, valid request with optional fields, invalid request (missing required field), invalid request (invalid data type), invalid request (validation failure), authenticated request from authorized user, authenticated request from unauthorized user (403 Forbidden), unauthenticated request (401 Unauthorized if required).

Request bodies must be generated using test fixtures that return valid Pydantic models. This ensures tests match the actual request validation rules.

Response assertions must verify status code, response structure (JSON keys and types), and key field values. When a POST endpoint creates a record, the response must include the created record with assigned ID and timestamp. When a GET endpoint returns a list, the response must include total count and items array.

Error responses must be tested to verify error messages are clear and do not expose sensitive information. HTTP 400 responses must include field-specific error messages for validation failures (field_name: error message).

Tests must verify authorization using role-based access control. A staff user cannot access admin-only endpoints. An adopter user cannot access staff-only endpoints. Only the adoption applicant can view their own adoption application details.

## Implementation Approach

Create a test_endpoints.py file that imports FastAPI TestClient and application fixtures. Organize tests by endpoint: test_list_animals, test_create_adoption_application, test_get_user_profile, etc.

For each endpoint, create multiple test functions using parameterized testing (pytest.mark.parametrize) to test multiple scenarios: valid request, missing field, invalid type, etc.

Use test fixtures to create request bodies and test data. Mock external dependencies like Stripe so tests do not make real API calls.

Test authentication by creating JWT tokens for different user roles and passing them in the Authorization header. Verify that endpoints reject requests without tokens or with invalid tokens.

Write assertions that check both happy path (status 200, expected data) and sad paths (status 400, error message).

## Success Criteria

All API endpoints have at least 5 test cases each covering happy path and multiple sad paths. Tests verify correct HTTP status codes (200, 201, 400, 401, 403, 404). Tests verify response JSON structure matches endpoint documentation. Tests verify authentication is enforced on protected endpoints. Tests verify role-based authorization prevents unauthorized access. All tests pass with 100% endpoint code coverage. Test execution completes in under 10 seconds.

