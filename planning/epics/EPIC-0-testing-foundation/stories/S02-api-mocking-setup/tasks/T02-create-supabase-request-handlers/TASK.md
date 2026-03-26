---
story: S02
task: T02
title: Create pytest Test Data Fixtures for FastAPI Endpoint Testing
status: pending
effort_hours: 2
priority: high
dependencies:
  - T01-configure-httpx-asyncclient-for-fastapi-testing
acceptance_criteria:
  - Animal fixture creates a test animal record in the database and returns its id
  - Donor fixture creates a test donor record with EUR currency and Dutch country code
  - Adoption application fixture creates a pending application linking a test animal to a test adopter
  - All fixtures clean up via the transaction rollback inherited from the db_session fixture
  - Fixtures are composable — the adoption application fixture can accept an animal and adopter fixture as arguments
  - Error scenario helpers exist for testing 401, 403, and 404 responses in endpoint tests
---

## Overview

Create shared pytest fixtures in tests/conftest.py that insert test data into the database for FastAPI endpoint testing. These fixtures replace the previously planned MSW Supabase request handlers, which were designed for a Next.js frontend that is no longer part of the tech stack. All test data in this project is created via SQLAlchemy and the real PostgreSQL test database, not via mocked HTTP responses.

## Why This Matters

FastAPI endpoint tests using httpx.AsyncClient with ASGITransport call the real FastAPI application, which reads from and writes to the test database. Tests that verify GET /animals must find actual records in the database. Tests that verify POST /adoption-applications must create records that can be queried back. Without shared fixture functions, every test file would define its own data setup, leading to duplication and inconsistency.

Centralizing test data creation in conftest.py ensures all tests use the same animal, donor, and application factory functions. The fixtures inherit database isolation from the db_session fixture (established in T02 of story S03), which wraps each test in a transaction that rolls back after the test. This means test data never persists between tests without any explicit cleanup.

## Context

The Refugio Animal Paraguay backend uses SQLAlchemy 2.x declarative models. The animals table, donors table, adoption_requests table, and related tables are defined as SQLAlchemy model classes in src/models. Test data factories call these model constructors and add records to the test database session. The test session is automatically rolled back after each test by the db_session fixture.

The fixture functions are not factory libraries — they are simple pytest fixtures that create one representative record per call. When a test needs a specific configuration (an animal with status "medical_hold", a donor with PYG currency), the fixture should accept override keyword arguments that get merged into the default values.

## Implementation Steps

### Step 1: Create the Animal Fixture

The animal fixture function in tests/conftest.py creates one animal record with sensible defaults. The animal name defaults to "Luna", species to "dog", breed to "mixed", status to "available", age in months to 24, gender to "female", and intake date to the current date. The fixture adds the animal to the db_session, flushes (to assign a database-generated id), and yields the animal object so the test can read its id and other fields. The flush is necessary because the database assigns the primary key and the test may need that key to construct request URLs.

The fixture accepts override keyword arguments. If a test passes species="cat" and name="Felix", those values replace the defaults before the record is inserted. This composability is essential for testing species-specific behavior.

### Step 2: Create the Donor Fixture

The donor fixture creates one donor record representing the primary donor persona: a Dutch EU donor. The defaults are full_name "Jan de Vries", email "jan.devries@example.nl", country "NL", preferred_currency "EUR", and is_active True. The fixture yields the donor object after flushing.

A second variant, the local_donor fixture, sets country to "PY" and preferred_currency to "PYG". This variant is used for testing Paraguayan donation flows, Tigo Money paths, and any currency-specific validation that differs between EUR and PYG.

### Step 3: Create the Adopter Fixture

The adopter fixture creates one adopter record with defaults: full_name "María García", email "maria.garcia@example.com", phone "+595 971 234567", city "Asunción", and has_outdoor_space True. The adopter is a registered user in the system with the adopter role, so the fixture also creates the corresponding users table record if the adopters table has a foreign key to users.

### Step 4: Create the Adoption Application Fixture

The adoption application fixture creates a pending application. It depends on both the animal fixture and the adopter fixture, so its signature receives those two objects as arguments. The application status defaults to "pending", application_date to the current date, and notes to an empty string.

If a test needs to verify the approval workflow, it calls this fixture and then directly updates the application record in the database session to status "under_review" before calling the endpoint. This is simpler than creating separate fixtures for each status transition.

### Step 5: Create Error Scenario Helpers

Error scenarios in FastAPI tests are produced by sending requests with incorrect headers, not by modifying fixtures. A helper function called make_request_without_auth returns a request coroutine that omits the Authorization header. A helper called make_request_with_wrong_role accepts a role name and returns auth headers signed for that role. These helpers are plain functions, not fixtures, defined in tests/conftest.py and importable from any test file.

For 404 scenarios, tests use an integer id that is guaranteed not to exist in the test database. The constant NONEXISTENT_ANIMAL_ID is defined in tests/conftest.py as a very large integer (such as 999999) that the test database id sequence will not reach during a test run.

### Step 6: Verify Fixture Composability

A test in tests/unit/test_fixtures.py confirms that the fixtures work together. One test creates an animal and an adopter, then creates an adoption application referencing both. The test asserts that the application record in the database has the correct animal_id and adopter_id. Another test creates an animal, sends a GET /animals/{id} request using the httpx.AsyncClient, and asserts the response body contains the animal's name and species. This confirms the full chain from fixture creation through FastAPI route to JSON response.

## Acceptance Criteria Verification

Running pytest tests/unit/test_fixtures.py passes without errors. The db_session fixture rollback behavior is confirmed: an animal created in one test is not visible in the next test. The donor fixture produces a record with country "NL" and preferred_currency "EUR" by default. The local_donor fixture produces a record with country "PY" and preferred_currency "PYG". The adoption application fixture accepts both an animal and an adopter object and creates a record linking them. The NONEXISTENT_ANIMAL_ID constant is defined and causes a 404 response when used in a GET /animals/{id} request.

## Common Issues and Solutions

If a fixture raises an IntegrityError about a unique constraint on the email column, the test database transaction is not being rolled back correctly. Verify that the db_session fixture uses a nested transaction (savepoint) and that each test function-scoped fixture creates its data within that nested transaction.

If the adoption application fixture reports a foreign key violation, the animal and adopter fixtures must flush their records before the adoption application fixture creates its record. Ensure that each fixture calls db_session.flush() after adding the model instance to the session.

If the animal fixture's default status value does not match the AnimalStatus enum defined in src/models, the fixture will raise a ValueError. Import the AnimalStatus enum at the top of conftest.py and use its members as default values rather than raw strings.

## Related Tasks

- S02/T01: Configure httpx AsyncClient for FastAPI Endpoint Testing — the client fixture must be working before these data fixtures are used in endpoint tests
- S03/T01: Configure database test session with rollback isolation — the db_session fixture must exist before any data fixture can use it
- S03/T02: Create shared conftest.py with all fixtures — consolidates all fixtures into one file

## References

- pytest fixtures documentation: docs.pytest.org/en/stable/reference/fixtures.html
- SQLAlchemy 2.x session usage: docs.sqlalchemy.org/en/20/orm/session_basics.html
- FastAPI testing guide: fastapi.tiangolo.com/tutorial/testing
