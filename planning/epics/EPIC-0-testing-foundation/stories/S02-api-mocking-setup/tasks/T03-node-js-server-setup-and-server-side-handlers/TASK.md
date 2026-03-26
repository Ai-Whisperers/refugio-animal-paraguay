---
epic: EPIC-0
story: S02
task: T03
title: Organize pytest Integration Test Module Structure
status: pending
effort_hours: 2
priority: high
dependencies:
  - T01-install-and-configure-msw-for-browser-tests
  - T02-create-supabase-request-handlers
---

## Overview

Establish the integration test module structure under tests/integration/ and document the patterns that all FastAPI integration test files must follow. Integration tests in this project differ from unit tests in two critical ways: they use the httpx.AsyncClient bound to the live FastAPI application via ASGITransport, and they interact with the test PostgreSQL database through the db_session fixture. This task defines where integration test files live, how they import shared fixtures, and what test organization patterns every integration test file must follow.

## Why This Matters

Without a consistent module structure, integration tests scatter across the project and teams cannot predict where to find or add test coverage for a given endpoint. Defining this structure now ensures that future test files for authentication, animal endpoints, adoption workflows, and donation flows all follow the same import conventions, fixture usage patterns, and assertion styles. The structure established here directly mirrors the organization used in S03 (database fixtures) and the FastAPI router organization in src/routers/.

## Context

The previous tasks (T01 and T02) established the httpx.AsyncClient fixture and the SQLAlchemy data fixtures in tests/conftest.py. Those fixtures are available to every test file automatically through pytest's conftest discovery mechanism. This task focuses on the integration test subdirectory structure, the pytest marker configuration that labels tests as integration tests, and the sample test files that demonstrate correct patterns for authentication and CRUD endpoint testing.

Integration tests are defined as tests that issue HTTP requests through the FastAPI application and verify responses based on data that exists in the test database. They are slower than unit tests and require a running PostgreSQL test database, so they are separated from unit tests and marked with the pytest.mark.integration marker so developers can run unit tests in isolation during rapid iteration.

## Implementation Steps

### Step 1: Create the Integration Test Directory

The integration test directory lives at tests/integration/ and contains one file per FastAPI router being tested. Each file name follows the pattern test_{router_name}.py, where router_name matches the module name in src/routers/. For example, the file that tests the animals router is tests/integration/test_animals.py, and the file that tests the auth router is tests/integration/test_auth.py. A __init__.py file in tests/integration/ is not required because pytest discovers tests through path configuration, but adding an empty one is acceptable.

### Step 2: Configure the Integration Test Marker

In pyproject.toml under the pytest configuration section, the integration marker must be declared with a description. The markers configuration key takes a list of strings, and the integration marker entry should read "integration: marks tests as integration tests requiring a running database and FastAPI application." This declaration prevents pytest from emitting warnings about unknown markers and documents the marker's purpose for new developers.

Integration tests are run separately from unit tests using the pytest -m integration flag. The default pytest run without flags should execute all tests. CI/CD pipelines may run unit tests and integration tests as separate steps to provide faster feedback on unit failures before waiting for slower integration tests.

### Step 3: Create the Auth Integration Test File

The file tests/integration/test_auth.py contains integration tests for all endpoints in the authentication router. Each test function is decorated with pytest.mark.integration and is an async function decorated with pytest.mark.anyio (or, if asyncio_mode is set to auto in pytest configuration, the async def alone is sufficient).

The test file imports the client fixture and the auth_headers fixtures from conftest.py via pytest's automatic fixture injection. It does not import the fixtures explicitly; it receives them as function arguments named client, admin_headers, staff_headers, and adopter_headers.

The test for a successful login sends a POST request to the auth endpoint (the actual path is determined by the FastAPI router definition in src/routers/auth.py) with a JSON body containing a valid email and password. The test asserts that the response status code is 200, that the response body contains an access_token field, and that the token_type field is the string "bearer". The test does not validate the contents of the JWT payload; it only verifies that a token is returned in the expected shape.

The test for login with invalid credentials sends a POST request to the same endpoint with a correct email but an incorrect password. The test asserts that the response status code is 401 and that the response body contains an error or detail field. The exact field name depends on how the FastAPI route formats error responses — this must match what the actual route returns.

The test for accessing a protected endpoint without a token sends a GET request to the authenticated user profile endpoint without any Authorization header. The test asserts that the status code is 401 and that the response body contains the FastAPI HTTPException detail string. This test verifies that the JWT dependency in FastAPI is wired correctly and rejects unauthenticated requests.

The test for accessing a protected endpoint with a valid token uses one of the auth_headers fixtures to send a GET request to the authenticated user profile endpoint. The test asserts that the status code is 200 and that the response body contains the user's email address, verifying that the JWT is decoded correctly and that the endpoint returns the authenticated user's data from the database.

### Step 4: Create the Animals Integration Test File

The file tests/integration/test_animals.py contains integration tests for the animals router. Each test is async and marked with pytest.mark.integration. The file receives the client fixture and the animal fixture from conftest.py.

The test for retrieving a list of animals sends a GET request to the animals collection endpoint and asserts that the response status code is 200 and that the response body is a JSON array. The test also asserts that the array is not empty when the animal fixture has been invoked, meaning a test animal was created before the request was sent. The animal fixture is added as a function argument to this test so pytest creates the database record before the HTTP request is issued.

The test for retrieving a single animal by ID sends a GET request to the animals detail endpoint using the animal fixture's database id. The URL is constructed by appending the id to the endpoint path. The test asserts that the response status code is 200 and that the response body contains the animal's name and species fields matching the values set by the animal fixture.

The test for retrieving a non-existent animal sends a GET request to the animals detail endpoint using the NONEXISTENT_ANIMAL_ID constant defined in conftest.py. The test asserts that the response status code is 404 and that the response body contains a detail field. This test verifies that the FastAPI route returns a proper HTTP 404 exception rather than returning an empty response or a 200 with null data.

The test for creating an animal sends a POST request to the animals collection endpoint with a JSON body describing a new animal. This endpoint requires authentication, so the test uses the staff_headers fixture to include an Authorization header. The test asserts that the response status code is 201 and that the response body contains the new animal's name and an id field assigned by the database. The test does not need to verify that the animal was committed to the database because the transaction rollback behavior means this animal will disappear after the test anyway; asserting the API response is sufficient.

The test for creating an animal without authentication sends the same POST request but without an Authorization header. The test asserts that the response status code is 401, verifying that the animals create endpoint requires a valid JWT.

The test for updating an animal sends a PATCH request to the animals detail endpoint using the animal fixture's id, with a JSON body containing a status field set to a different value than the fixture's default. The test uses staff_headers for the Authorization header and asserts that the response status code is 200 and that the response body contains the updated status value.

### Step 5: Create the File Upload Integration Test File

The file tests/integration/test_photos.py contains integration tests for the animal photo upload endpoint. The test for uploading a photo sends a POST request to the photo upload endpoint with a multipart form body containing a small synthetic image binary and a filename. The test uses staff_headers for authorization and asserts that the response status code is 201 and that the response body contains a file identifier or URL field.

The test for uploading a photo without authentication sends the same multipart POST without an Authorization header and asserts that the response status code is 401.

The test for retrieving photos for an animal sends a GET request to the animal photos listing endpoint using an animal fixture's id and asserts that the response status code is 200 and that the response body is a JSON array (which may be empty if no photos were uploaded within the current transaction).

### Step 6: Write Fixture Lifecycle Documentation

A comment block at the top of each integration test file explains the fixture lifecycle for that file. The comment describes which fixtures the file uses, confirms that all database records created by fixtures are rolled back after each test function, and notes that the httpx.AsyncClient is created fresh for each test function with ASGITransport binding it directly to the FastAPI application object. This documentation helps new contributors understand why test data from one test does not appear in the next test.

### Step 7: Verify Test Discovery

After creating the test files, run pytest --collect-only tests/integration/ to verify that all test functions are discovered correctly. The output should list each test function with its full path. If pytest reports "no tests ran" or collection errors, the most common causes are incorrect asyncio_mode configuration, missing fixtures, or incorrect marker declarations in pyproject.toml.

## Acceptance Criteria

- tests/integration/ directory exists and contains test_auth.py, test_animals.py, and test_photos.py
- All test functions in tests/integration/ are decorated or configured for async execution and succeed when run with pytest tests/integration/
- The pytest.mark.integration marker is declared in pyproject.toml with a description and produces no marker warnings when tests run
- The test for GET /animals/{id} with a valid database id returns 200 and the animal's name field
- The test for GET /animals/{id} with NONEXISTENT_ANIMAL_ID returns 404
- The test for POST /animals without an Authorization header returns 401
- The test for POST /animals with staff_headers returns 201
- Running pytest tests/ executes both unit and integration tests; running pytest -m integration executes only integration tests; running pytest -m "not integration" executes only unit tests
- All test files contain the fixture lifecycle comment block explaining rollback behavior

## Common Issues and Solutions

If an integration test receives a 404 for an endpoint that should exist, the FastAPI router may not be included in the application's router registration. Check that the router for the endpoint under test is mounted in the main FastAPI application factory function in src/main.py.

If an integration test receives a 422 Unprocessable Entity response when creating a resource, the JSON body sent in the test does not match the Pydantic schema that the route expects. Compare the request body in the test against the Pydantic model defined in src/schemas/ for that resource.

If fixture data created in a test appears to persist into the next test, the db_session fixture may not be configured with the SAVEPOINT-based rollback pattern. Verify that the db_session fixture in conftest.py begins a savepoint at the start and rolls back to that savepoint after each test, not a top-level transaction that only commits at the end of the session.

If the client fixture raises an error about the event loop being closed, the anyio backend must be set to asyncio consistently across all async test functions. Verify that the asyncio_mode configuration in pyproject.toml is set to auto, which removes the need for the pytest.mark.anyio decorator on every test function.

## Related Tasks

- S02/T01: Configure httpx AsyncClient for FastAPI Endpoint Testing — the client fixture this task depends on
- S02/T02: Create pytest Test Data Fixtures — the animal, donor, adopter, and adoption application fixtures used in integration tests
- S03/T01: Configure database test session with rollback isolation — the db_session fixture that this task's fixtures depend on

## References

- pytest integration test organization: docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-files
- pytest custom markers: docs.pytest.org/en/stable/how-to/mark.html
- pytest-anyio configuration: anyio.readthedocs.io/en/stable/testing.html
- FastAPI testing guide: fastapi.tiangolo.com/tutorial/testing
