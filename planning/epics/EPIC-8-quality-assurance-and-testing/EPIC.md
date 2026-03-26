---
epic: EPIC-8
title: Quality Assurance & Testing
status: ready
created: 2026-03-25T17:13:26.734780
updated: 2026-03-25T17:13:26.734783
---

# EPIC-8: Quality Assurance & Testing

## Overview

**Goal**: Establish a comprehensive, automated testing strategy that verifies every layer of the platform — from individual validation functions through full user workflows — and integrates quality gates into the development process so that defects are caught before they reach production.

**Why it matters**: A shelter platform that loses adoption records, miscounts donation totals, or silently fails to deliver notification events is worse than no platform at all — the shelter owner would have more confidence in their spreadsheet. Testing is not a phase that happens at the end; it is the continuous discipline that makes each feature reliable enough to trust. For a small team where no single person can review every change, automated tests are the safety net that allows the codebase to grow without accumulating hidden defects. The European donor audience in particular expects professional-grade reliability from a platform that handles their payment information.

**Target users**: Developers who run the test suite to verify changes before committing; the CI/CD pipeline (EPIC-9) that runs the full suite on every pull request; shelter administrators who benefit from a stable, trustworthy system; ultimately, adopters, donors, and volunteers who rely on the platform working correctly.

---

## Scope

### In Scope

- Unit test suite covering all validation functions, business logic, data transformation utilities, and domain rule enforcement; using pytest with synchronous and asynchronous test cases as appropriate to the code under test
- Integration test suite covering all FastAPI route handlers using httpx AsyncClient against a real test database provisioned by Alembic migrations; testing authentication enforcement, request validation, response schemas, and error cases for each endpoint
- PostgreSQL trigger and LISTEN/NOTIFY tests covering the database-level event functions that power the real-time activity feed in EPIC-7; these are tested with a real test database because they cannot be meaningfully exercised with mocks
- End-to-end workflow tests for the two highest-value user journeys: the complete adoption lifecycle from animal discovery through application submission to staff approval and notification delivery, and the complete donation lifecycle from amount selection through Stripe payment (test mode) through webhook processing to confirmation email
- Component testing strategy documentation for the frontend, specifying what behaviors need coverage once the frontend technology stack is chosen (EPIC-11); this document defines the test requirements without yet implementing the tests
- Performance baseline testing using locust to measure API response times under simulated concurrent load, establishing the performance budgets that production deployments are held to
- Security scanning integration: bandit for Python static analysis, pip-audit for dependency vulnerability checking, and gitleaks for secret detection; all three are run as part of the CI pipeline defined in EPIC-9
- Test fixture library: shared pytest fixtures for creating test users with each role, seeding a test animal, creating a test adoption application, and simulating a completed Stripe payment; these fixtures are available to all test modules via conftest.py

### Out of Scope

- Manual exploratory testing protocols (valuable but not automated; the shelter owner and staff perform these informally before each release)
- Accessibility testing automation (important but deferred to when the frontend is built in EPIC-11)
- Load testing at production scale (the performance baseline tests establish targets; full load testing would require a staging environment with production-equivalent data volume)
- Test data generation for non-engineering purposes (the shelter uses real data once live)
- Chaos engineering or fault injection testing

---

## Stories

- **S01: Unit & Integration Test Suite** — Implement the pytest test suite structure with separate directories for unit and integration tests and a shared conftest.py for fixtures. Write unit tests for all validation functions across all modules (email format, phone number format, status transition rules, pagination calculation, role permission checks). Write integration tests for all FastAPI endpoints using httpx AsyncClient with JWT fixtures for each role. Implement the test database setup and teardown pattern using Alembic migrations applied to a dedicated test PostgreSQL database. Verify that every test uses the Arrange-Act-Assert pattern. Establish the 80 percent coverage threshold as the minimum acceptable baseline.

- **S02: Component Testing** — Document the component testing strategy for the frontend application. Define the specific behaviors that must be covered: adoption form submission with valid and invalid inputs, donation amount selection and currency display, volunteer shift sign-up and capacity enforcement feedback, admin dashboard table rendering with pagination, and error state rendering when API calls fail. This story produces a specification document rather than implemented tests, because the frontend technology stack has not yet been selected. When EPIC-11 begins, this document serves as the testing requirements for the frontend team.

- **S03: End-to-End Testing** — Implement the adoption workflow E2E test that exercises the complete sequence: an unauthenticated user queries the animal catalog, finds an available animal, submits an adoption application, the system sets the animal to reserved, an authenticated staff user reviews and approves the application, the notification service emits a confirmation event, and the adoption record reflects the approved status with the correct timestamps and staff attribution. Implement the donation workflow E2E test that exercises the sequence: a donor submits a donation amount, the platform creates a Stripe PaymentIntent in test mode, the test simulates the Stripe webhook for payment confirmation, the donation record is created, and the notification service emits a receipt event. Both tests run against a real test database and the test Stripe environment.

- **S04: Performance & Security Testing** — Define the performance budget for each category of API endpoint based on the success metrics in EPIC-1, EPIC-2, and EPIC-7: catalog endpoints at p95 under 200 milliseconds, individual record endpoints at p95 under 100 milliseconds, report aggregate endpoints at p95 under 500 milliseconds. Implement locust load test scenarios for the animal catalog endpoint and the adoption application submission endpoint. Configure bandit to run against the entire Python source tree with a severity threshold that fails the CI pipeline on medium or higher findings. Configure pip-audit to fail the CI pipeline on any known vulnerability with a high or critical CVSS score. Configure gitleaks to scan the repository history for accidentally committed secrets.

---

## Dependencies

**Depends on**:
- EPIC-1 (Animal Catalog) — the test suite exercises catalog and search endpoints
- EPIC-2 (Adoption Process) — the adoption E2E test exercises the full application and approval flow
- EPIC-3 (Donations) — the donation E2E test exercises the Stripe payment and webhook flow
- EPIC-5 (Volunteer Management) — integration tests cover shift sign-up and capacity enforcement
- EPIC-10 (Authentication) — all role-based endpoint tests require JWT fixtures for each role
- EPIC-9 (CI/CD) — the test pipeline is run by the GitHub Actions configuration defined in EPIC-9; performance and security scans are integrated into the CI pipeline

**Blocks**:
- Nothing; EPIC-8 is cross-cutting and runs alongside all other epics throughout development, not after them

---

## Success Metrics

- The unit and integration test suite runs to completion in under four minutes on the CI pipeline, fast enough to provide feedback on every pull request without creating queue delays
- Overall line coverage is at or above 80 percent at all times; the CI pipeline blocks any merge that would decrease coverage below this threshold
- The adoption E2E test and the donation E2E test pass on every commit to the develop branch, providing continuous confidence that the two most critical user workflows are functional
- Zero high or critical security findings from bandit or pip-audit on any release branch commit
- The performance budget tests confirm that the catalog endpoint meets the p95 under 200 milliseconds target under a simulated load of 50 concurrent users

---

## Risk Factors

- **Test database isolation**: Integration tests that share a single test database can interfere with each other if transaction rollback boundaries are not carefully managed. Mitigation: each integration test runs within a transaction that is rolled back at test teardown; tests that specifically test transaction semantics (such as concurrent adoption reservation) use separate database connections and explicit cleanup.
- **Stripe test mode divergence**: Stripe's test mode may not reproduce all edge cases of the live payment API (particularly webhook signature verification and certain error response codes). Mitigation: the donation E2E test uses the Stripe test webhook CLI tool to replay real webhook payloads rather than manually constructing webhook bodies; this ensures that webhook signature verification is tested with real signatures.
- **Slow E2E tests discouraging use**: End-to-end tests that take more than 30 seconds each will be skipped by developers under time pressure. Mitigation: optimize E2E tests to avoid unnecessary waits; run E2E tests only in the CI pipeline, not as part of the local pre-commit hook; use pytest markers to allow developers to run only unit tests locally.
- **Coverage false confidence**: High coverage percentage does not guarantee that the right behaviors are tested. A test that calls a function but makes no meaningful assertion will count toward coverage while catching no bugs. Mitigation: require every test to have at least one assertion that would fail if the code under test were broken; this is enforced by code review rather than automation.

---

## Effort & Priority

**Priority**: Cross-cutting and ongoing. Testing is not a single sprint of work; it is a discipline applied to each feature epic as it is developed. Unit and integration tests for each new endpoint should be written in the same sprint as the endpoint. E2E tests are written in EPIC-8's dedicated sprint once EPIC-2 and EPIC-3 are functionally complete. Performance and security scanning is configured once during EPIC-9's CI/CD setup sprint and maintained thereafter.

**Estimated effort**: One dedicated sprint for the E2E tests and performance/security scanning configuration (S03, S04). S01 and S02 are developed incrementally alongside each feature epic rather than in a single block.
