---
story: S02
task: T01
title: Configure httpx AsyncClient for FastAPI Endpoint Testing
status: pending
effort_hours: 3
priority: high
dependencies: []
acceptance_criteria:
  - httpx installed as a dev dependency alongside pytest-asyncio
  - A shared client fixture in conftest.py creates an AsyncClient via ASGITransport
  - At least one endpoint test passes using the shared client fixture
  - Auth header fixture generates valid JWT tokens for each role
  - No real network connections are made during any test run
---

## Overview

Configure httpx with ASGITransport so that FastAPI endpoint tests call the app in-process without a running server. This replaces the previously planned MSW service worker setup, which applied to a Next.js frontend that is no longer part of the tech stack. All HTTP testing in this project targets the FastAPI backend using Python's httpx library.

## Why This Matters

FastAPI applications are best tested by binding an httpx.AsyncClient directly to the app object using ASGITransport. This approach means tests call real FastAPI routes, execute real dependency injection, validate Pydantic schemas, and interact with the database — without starting a TCP server on a network port. Tests run faster, are more deterministic, and do not require port allocation or teardown logic.

Without a proper client fixture, every test file would need to manage its own client lifecycle, leading to code duplication and inconsistent teardown. Centralizing the client in conftest.py ensures all tests share the same reliable setup.

## Context

The Refugio Animal Paraguay backend is a FastAPI application with async route handlers. Tests need to send HTTP requests to endpoints such as POST /animals, GET /animals, POST /auth/login, POST /donations, and others defined in the route layer. Each request must carry appropriate authentication headers where the endpoint requires a logged-in user.

The ASGITransport approach means the client communicates with FastAPI via the ASGI interface in memory rather than over a socket. The database session is injected via FastAPI's dependency overrides so that tests use a transaction-wrapped session that rolls back after each test.

## Implementation Steps

### Step 1: Install Required Packages

The dev dependencies that must be added to pyproject.toml or requirements-dev.txt are: httpx (version 0.27 or later), pytest-asyncio (version 0.23 or later), and anyio with the trio extra for async test support. These are installed into the virtual environment using pip. After installation, running pytest --collect-only from the project root should discover test files without import errors.

### Step 2: Configure pytest for Async Mode

The pyproject.toml file must include a tool.pytest.ini_options section that sets asyncio_mode to "auto". This setting causes pytest-asyncio to treat all async test functions as coroutines automatically, without requiring the @pytest.mark.asyncio decorator on every test. The testpaths key should point to the tests directory. The filterwarnings key should silence deprecation warnings from SQLAlchemy and Pydantic during test runs.

### Step 3: Create the Client Fixture

The tests/conftest.py file at the project root defines the shared fixtures. The client fixture is an async fixture with function scope. It imports the FastAPI app object from src.main and creates an httpx.AsyncClient using httpx.ASGITransport with the app as its argument and base_url set to http://test. The fixture uses an async context manager (async with) so that the client is properly started and closed around each test. The db_session fixture must be created first (see T02) because the client fixture overrides the app's get_db dependency to inject the test session.

### Step 4: Create Auth Header Fixtures

The conftest.py file also defines auth header fixtures for each user role. Each fixture creates a test user in the database with the appropriate role, calls the login endpoint via the client to obtain a JWT token, and returns a dictionary containing the Authorization header in Bearer format. The roles that need fixtures are: admin_headers, staff_headers, vet_headers, volunteer_headers, adopter_headers, and foster_headers. These fixtures have module scope so that the test user and token are created once per test module rather than once per test function.

### Step 5: Write a Verification Test

A file at tests/unit/test_client_setup.py should contain a single test that calls GET /health on the FastAPI app and asserts the response status code is 200. This test does not require authentication and confirms that the client fixture is working correctly. The health endpoint returns a JSON object with a status field set to "ok" and a db_connected field confirming the database session is available.

## Acceptance Criteria Verification

- Running pip show httpx from inside the virtual environment shows a version of 0.27 or later installed
- The tests/conftest.py file exists and contains an async client fixture that uses ASGITransport
- Running pytest tests/unit/test_client_setup.py passes without errors
- The admin_headers fixture generates a token that grants access to admin-only endpoints in subsequent tests
- No test output contains lines matching "connecting to" or "tcp" indicating real network connections

## Common Issues and Solutions

If pytest reports "ScopeMismatch: You tried to access the function scoped fixture client from the session scoped fixture", the auth fixtures must be changed from session scope to module scope, or the client fixture must be promoted to session scope with care taken that the database transaction is still isolated between tests.

If httpx raises "ValueError: Transport already closed", the async with block managing the client is not being awaited correctly. Verify that the fixture uses yield inside an async with block rather than return.

If the FastAPI app cannot be imported in conftest.py due to missing environment variables, ensure the test environment loads a .env.test file before the app module is imported. This is done by setting the DOTENV_PATH environment variable before running pytest, or by using a conftest.py autouse fixture that calls python-dotenv's load_dotenv before the app import.

## Related Tasks

- S02/T02: Configure database test session with rollback isolation — must be completed before the client fixture can override the database dependency
- S02/T03: Configure pytest-cov for coverage measurement — uses the same pytest configuration established in this task

## References

- httpx documentation for ASGITransport: httpx.encode.io/advanced/transports
- FastAPI testing documentation: fastapi.tiangolo.com/tutorial/testing
- pytest-asyncio documentation: pytest-asyncio.readthedocs.io
