---
task: T01
story: S02
epic: EPIC-7
title: Create user management UI
---

# T01 — User Management Interface (Admin API)

## Objective

Implement the backend API that powers the admin user management interface, providing paginated, searchable, and filterable access to all user accounts in the system.

## Background and Rationale

Shelter administrators need to view and manage all user accounts — staff, adopters, and other admins — from a central interface. This task implements the FastAPI endpoint that backs the user management table in the admin dashboard. It handles search, role filtering, and pagination server-side so the frontend receives exactly the data it needs to display one page of results.

## API Endpoint

The endpoint is registered in the admin router at `GET /admin/users`. It accepts three optional query parameters: `q` for a search string, `role` to filter by a specific role value, and `page` for the page number (defaulting to one if omitted).

Access is restricted to users with the `admin` role. The route uses a FastAPI dependency called `require_admin_role` that extracts the JWT token from the Authorization header, decodes it, and raises a 403 Forbidden response if the authenticated user does not hold the admin role. This dependency is applied at the router level so every endpoint in the admin router inherits it automatically.

## SQLAlchemy Query Logic

The service layer builds a SQLAlchemy query against the `users` table. All query parameters are optional and additive — each one that is provided narrows the result set further.

When the `q` parameter is present, the query adds an OR condition using PostgreSQL's case-insensitive `ilike` operator on both the `full_name` column and the `email` column. This means searching for "maria" will match users whose full name or email address contains that string in any case.

When the `role` parameter is present, the query adds an exact match condition against the `role` enum column on the users table.

Pagination uses a fixed page size of twenty records. The query computes the offset as `(page - 1) * 20` and applies both the offset and the limit to the SQLAlchemy query. A separate count query using SQLAlchemy's `func.count` runs against the same filter conditions (without limit/offset) to determine the total number of matching records. The total page count is derived from this total count divided by the page size, rounded up.

## Response Schema

The endpoint returns a Pydantic model called `UserListResponse` that contains four fields: a `users` field holding a list of `UserSummary` objects, a `total_count` integer representing the total number of matching users across all pages, a `page` integer reflecting the current page number, and a `total_pages` integer.

Each `UserSummary` object contains the fields needed for the management table: the user's UUID, full name, email address, role, and the `created_at` timestamp representing when they registered.

## Frontend Integration

The frontend (stack TBD) renders the user management interface as a table with columns for Name, Email, Role, and the date the user joined. Above the table, a text search input and a role dropdown filter allow the admin to narrow the list. Changes to either filter reset the page to one and update the URL query parameters, which triggers a new fetch to the API endpoint.

The frontend passes the current search text as `q`, the selected role as `role`, and the current page number as `page` in the query string. On each response, the frontend reads `total_pages` to determine how many pagination buttons to render and uses `total_count` to display a summary such as "Showing 21–40 of 83 users."

## Error Handling

If the `page` parameter is less than one or greater than `total_pages`, the endpoint returns a 400 Bad Request response with a clear message. If the `role` parameter is provided but does not match a valid role enum value, the endpoint returns a 422 Unprocessable Entity response, which Pydantic generates automatically from the schema validation.

A missing or invalid JWT token results in a 401 Unauthorized response. A valid token belonging to a non-admin user results in a 403 Forbidden response, both handled by the `require_admin_role` dependency.

## Testing Strategy

Unit tests cover the service layer functions responsible for building the filtered and paginated SQLAlchemy query. These tests verify that providing a `q` string results in an `ilike` condition on both `full_name` and `email`, that providing a `role` string adds an exact match condition, and that the offset calculation is correct for various page numbers.

Integration tests run against a real PostgreSQL test database. One test seeds the database with a known set of users across multiple roles, then calls the endpoint with various combinations of `q`, `role`, and `page` parameters, and asserts that the response contains the expected users and correct pagination metadata. Another integration test verifies pagination boundaries: requesting a page beyond `total_pages` returns 400, and requesting page one of a zero-result search returns an empty `users` list with `total_count` of zero and `total_pages` of zero.

A separate integration test verifies the authentication guard: a request without a JWT token receives 401, and a request with a valid staff-role token (not admin) receives 403.

## Files Involved

The endpoint route definition lives in the admin router module. The service layer function that builds and executes the query lives in a user service module under `src/users/`. The Pydantic response schemas live in the schemas module. The `require_admin_role` dependency lives in the auth dependencies module and is shared across all admin routes.
