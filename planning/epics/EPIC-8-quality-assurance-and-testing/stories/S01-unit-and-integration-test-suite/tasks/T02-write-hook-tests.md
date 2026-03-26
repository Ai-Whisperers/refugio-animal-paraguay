---
task: T02
story: S01
epic: EPIC-8
title: Write hook tests
status: ready
priority: medium
created: 2026-03-25T17:13:26.735057
---

# T02: Write hook tests

## Description

Create the unit and integration test suite that covers PostgreSQL trigger functions, Alembic migration lifecycle, the LISTEN/NOTIFY notification pathway, and SQLAlchemy event listeners used by the application. These tests ensure that the database-side behavior — which operates below the FastAPI layer — is correct and verifiable in isolation.

## Approach

This test file lives under `tests/unit/` for pure logic tests and `tests/integration/` for tests that require a real database connection. The distinction matters: tests that verify Python logic around database events can use mock objects and run fast in isolation, while tests that verify that a PostgreSQL trigger actually fires must connect to a real test database instance.

All tests use pytest. Integration tests in this file are marked with the `integration` marker so they can be excluded from the fast unit test run and included in the full CI run.

## PostgreSQL Trigger Function Tests

The real-time activity feed relies on a PostgreSQL trigger that fires after INSERT operations on the `adoption_requests` and `donations` tables. The trigger calls a notify function that constructs a JSON payload and passes it to `pg_notify`.

The trigger function test connects to the test database, inserts a record into `adoption_requests`, and then checks that the notify channel received a message. The test uses asyncpg to listen on the `admin_activity` channel before inserting the record, then waits briefly for the notification to arrive, and finally asserts that the payload matches the expected shape: it must contain a `type` field with the value `adoption`, a `description` field summarizing the event, and an `occurred_at` timestamp.

The same test pattern is repeated for insertions into the `donations` table, verifying that the payload type is `donation` and the description reflects the donation amount and currency.

A negative test verifies that an UPDATE or DELETE operation on those tables does not fire the notify trigger, confirming the trigger is scoped to INSERT only as intended.

## Alembic Migration Tests

Every Alembic migration must be testable in both the forward and backward direction. The migration test module keeps a list of all migration revision identifiers and verifies that each one can be applied and rolled back cleanly against the test database.

The forward migration test applies each migration in sequence and verifies that the expected tables, columns, and constraints exist after application. For migrations that add PostgreSQL trigger functions, the test queries the `pg_trigger` and `pg_proc` system catalog tables to confirm the trigger and function were created.

The rollback migration test calls the Alembic downgrade operation for each migration and verifies that the schema returns to its prior state. For trigger migrations, the downgrade test confirms that the trigger and function have been removed from the catalog.

The migration tests run in a transaction that is rolled back after each test, preventing migration state from persisting between tests and keeping the test database clean.

## asyncpg LISTEN/NOTIFY Integration Tests

The FastAPI background task that powers the admin activity WebSocket subscribes to the PostgreSQL notification channel using asyncpg. The integration test for this pathway verifies the full subscriber lifecycle.

The test creates an asyncpg connection, registers a listener on the `admin_activity` channel, then triggers a notification by inserting a record via a separate connection. The test asserts that the listener callback is invoked within a timeout period and that the payload it receives is a valid JSON string matching the expected event schema.

A connection failure test simulates an asyncpg connection drop by closing the underlying connection mid-listen and verifies that the application code handles the exception without crashing, either by re-raising a structured error or by triggering the reconnection logic defined in the WebSocket handler.

## SQLAlchemy Event Listener Tests

The application uses SQLAlchemy `after_insert` event listeners on certain model classes to trigger side effects such as enqueueing email notifications. These listeners attach to the SQLAlchemy session machinery and fire after a successful flush.

The event listener unit tests mock the SQLAlchemy session and event system using `unittest.mock.patch` targeting the specific import path within the listener module. Each test invokes the listener function directly with a mock mapper, connection, and target instance, then asserts that the expected downstream function was called with the correct arguments.

The integration variant of these tests uses the real test database session and verifies that inserting a model instance via SQLAlchemy triggers the listener and that the side effect function records the expected state — for example, that a notification record appears in the `notification_log` table after an adoption request is inserted.

## Notify Payload Builder Unit Tests

The function that constructs the JSON payload for `pg_notify` is pure Python and can be tested entirely without a database connection. These unit tests are in `tests/unit/` and verify every field of the payload for both adoption and donation event types.

Tests cover the normal case where all fields are present and valid, the edge case where optional fields such as adopter display name are None and must be omitted or replaced with a default, and the case where the timestamp is formatted as an ISO 8601 string in UTC rather than in the local server timezone.

## Coverage Expectation

The hook and migration test module targets eighty percent coverage of the trigger utility functions, notify payload builder, and SQLAlchemy event listener modules. Migration tests themselves are exempt from the line coverage threshold since their primary value is verifying schema state rather than line execution, but every migration revision must have at least a forward-and-back test case.
