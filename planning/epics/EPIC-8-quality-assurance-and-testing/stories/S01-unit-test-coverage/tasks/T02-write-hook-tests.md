---
task_id: T02
task_title: Write SQLAlchemy ORM Event Hook Tests for Audit Logging
task_status: pending
story_id: S01
epic_id: EPIC-8
created_date: 2026-03-25
estimated_effort: 8 hours
dependencies:
  - T02-implement-adoption-workflow (EPIC-1-S02)
  - T01-implement-donation-workflow (EPIC-3-S02)
  - T01-write-api-tests.md (EPIC-8-S01-T01)
---

## Overview

SQLAlchemy ORM event hooks are database operation interceptors that trigger custom logic when entity state changes occur. The Refugio Animal Paraguay system uses ORM event hooks to implement automatic audit logging, which tracks who changed what and when across all critical database tables. This task involves writing comprehensive unit tests that verify ORM hooks execute correctly, that audit log records are created with accurate metadata, and that hook failures are handled appropriately without disrupting normal application flow.

Testing ORM hooks requires a different approach than testing business logic functions or API endpoints because hooks execute as side effects during SQLAlchemy session operations. Tests must verify that when an adoption record is created, updated, or deleted, corresponding audit log entries appear with correct timestamps, user identifiers, and change descriptions. Tests must also verify that hooks handle edge cases properly, such as bulk operations, session rollbacks, and concurrent modifications.

The test suite focuses on four critical hook scenarios: the after-insert hook that logs new record creation, the after-update hook that logs field modifications with before/after values, the after-delete hook that logs record removal, and the before-flush hook that captures user context from the application session. Tests validate that audit logs accurately represent database changes, that user information is correctly associated with changes, and that hooks do not introduce performance regressions or data corruption.

## Why This Task Matters

Audit logging is foundational to institutional accountability, regulatory compliance, and troubleshooting. When a donor questions why their donation status changed or when staff members need to understand the complete history of an adoption request, audit logs provide the single source of truth. Without proper testing of the hooks that generate these logs, the system cannot guarantee data integrity or audit trail completeness.

ORM hooks are particularly error-prone to test because they execute during session operations in ways that are not always visible. A hook that works correctly in manual testing might fail under load, during concurrent modifications, or when session state changes unexpectedly. Poor hook testing leads to missing audit records, incomplete change histories, or hooks that crash silently and cause subtle data inconsistencies.

Testing hooks early in the development cycle catches integration issues before they propagate through the system. Hook tests serve as executable specifications that document exactly what database changes trigger audit logging and what information is captured. These tests also protect against regressions when ORM libraries are upgraded or when hook logic is modified.

## Technical Requirements

The hook test suite covers adoption, donor, and donation entities, which are the primary audit targets. Tests organize into logical groups by hook type and entity.

The after-insert hook test for adoption records verifies that when an adoption request is created with a specific adopter identifier, animal identifier, and request reason, an audit log entry is automatically created with an operation type of create, a timestamp matching or very close to the database insertion time, the user identifier extracted from the application session context, the entity type set to adoption-request, the entity identifier matching the newly created adoption request, and a change description documenting the new adoption request creation with relevant details like adopter email and animal type.

The after-update hook test for adoption status changes verifies that when an adoption request status transitions from pending to approved or another valid state change, an audit log entry is created with an operation type of update, the user identifier of the staff member making the change, a change description capturing both the old status and new status, the old value field showing the previous status, and the new value field showing the status after the update. This test verifies that hook execution happens after the database commit, preventing inconsistent states where the audit log is created but the status update fails.

The after-update hook test for donation amount modifications verifies that when a recurring donation amount is changed, the audit log captures the monetary change with both the previous amount in cents and the new amount in cents, the currency code, the user who authorized the change, and a timestamp. Tests include both direct column updates via ORM and bulk updates via query expressions to ensure hooks capture both operation types.

The after-delete hook test for adoption record deletion verifies that when an adoption request is deleted via the ORM, an audit log entry with operation type delete is created before the deletion is finalized, the entity identifier of the deleted record is preserved in the audit log, the timestamp captures when the deletion occurred, and the user identifier captures who authorized the deletion. Tests verify that deletion audit entries can reference deleted entity data through the audit log's archived values field.

The before-flush hook test verifies that user context from the application session is correctly captured and made available to after-operation hooks. This test creates a session context that associates a user identifier with database operations, performs entity modifications, flushes the session, and verifies that audit log entries created during the flush operation have the correct user identifier.

Concurrent modification tests verify that when multiple requests modify the same entity nearly simultaneously, audit log entries are created in the correct order with distinct timestamps, no audit log entries are lost due to race conditions, and the audit log accurately represents the sequence of changes. These tests use threading or async operations to simulate concurrent requests.

Bulk operation tests verify that when multiple adoption records are updated in a single query operation via query expressions, audit log entries are created for each affected entity rather than a single bulk operation entry. Tests verify that bulk operations do not cause the hook system to lose track of individual entity modifications.

Session rollback tests verify that when a transaction is rolled back due to an error, any audit log entries created within that transaction are also rolled back and do not appear in the final database state. This ensures that the audit trail only contains committed changes.

Error handling tests verify that when an ORM hook raises an exception, the exception is propagated to the application layer without silencing or swallowing the error. Tests verify that hook errors prevent the database operation from completing, protecting data integrity. Tests also verify that cleanup operations in hooks execute correctly even when exceptions occur.

Performance tests verify that audit logging overhead does not introduce significant latency to database operations. Tests measure the time to create, update, and delete entities with and without hooks enabled, establishing baseline performance metrics to catch regressions when hook logic becomes more complex.

All hook tests use a test database with the hook system enabled to ensure tests validate the actual hook behavior rather than mock approximations. Tests use SQLAlchemy session fixtures that isolate each test case with independent transactions that are rolled back after test completion, preventing test interdependencies.

## Implementation Approach

Hook tests are organized within the test suite under tests/unit/hooks/ with files structured by entity type. The adoption-hooks-test.py file contains tests for after-insert, after-update, and after-delete hooks that operate on adoption records. The donation-hooks-test.py file contains tests for donation entity modifications. The context-hooks-test.py file contains tests for the before-flush hook that captures user session context.

Each hook test begins with a fixture that sets up a clean database session, establishes a user context within the session (typically using a context variable or session attribute that the before-flush hook reads), and provides access to the audit log table for assertions. The fixture returns a tuple containing the session object, the user identifier, and the audit log query builder.

For the after-insert hook test on adoption records, the test creates a new adoption request entity with specific field values, adds it to the session, flushes the session to trigger hook execution, queries the audit log table for entries matching the adoption entity identifier, and asserts that exactly one audit log entry exists with operation type create, correct timestamp, correct user identifier, and a change description containing relevant adoption details.

For the after-update hook test on adoption status changes, the test retrieves an existing adoption record from the database, modifies its status field to a new valid state, flushes the session, queries the audit log for entries matching the adoption identifier and update operation type, and asserts that an audit log entry exists with the correct old status and new status values captured. The test also verifies that other fields not modified do not appear in the change description.

For concurrent modification tests, the test uses a threading module to simulate multiple requests modifying the same adoption record. The test creates an adoption record, spawns multiple threads that each retrieve the record and perform different modifications such as status changes or note updates, allows threads to execute concurrently, collects all audit log entries created during the concurrent execution, and verifies that all changes are recorded in chronological order with distinct timestamps and that no entries are lost.

For bulk operation tests, the test uses SQLAlchemy update expressions to modify multiple adoption records based on a query condition, such as updating all pending adoptions to a specific status, executes the bulk update, queries the audit log, and verifies that an audit log entry is created for each affected adoption record rather than a single bulk operation entry. The test compares the number of affected rows returned by the bulk update to the number of audit log entries created to ensure completeness.

For session rollback tests, the test executes database operations within a transaction context, deliberately triggers an error condition such as a constraint violation, catches the exception and rolls back the session, queries the audit log for entries created during the failed transaction, and asserts that the audit log contains no entries from the rolled-back transaction.

For error handling tests, the test modifies the hook logic to raise an exception on specific conditions, such as when a particular entity field has a certain value, executes the operation that triggers the exception, catches the exception at the application layer, and verifies that the database operation failed and was rolled back.

Test assertions focus on verifying audit log content accuracy, including checking that operation type matches the database operation performed, timestamps are within an acceptable range of the actual modification time, user identifiers are correctly captured from the session context, entity identifiers match the modified records, and change descriptions or before/after values accurately represent the modifications.

Tests use parametrization to cover multiple entity types and operation combinations. For example, a single test function can be parameterized to run the same hook test logic against adoption, donation, and donor entities, verifying that the hook system works correctly across all auditable entity types.

## Success Criteria

The hook test suite achieves ninety percent code coverage for all ORM event hook implementations, including after-insert, after-update, after-delete, and before-flush hooks. Coverage includes all conditional branches within hooks, such as the logic that determines whether a modification is significant enough to log and the logic that extracts user context from session state.

All hook test cases execute without failures or errors. This includes after-insert tests for adoption, donation, and donor entities, after-update tests for status changes and amount modifications, after-delete tests confirming deletion logging, and context capture tests verifying user association.

Tests verify that audit log entries are created with completely accurate data including operation types, timestamps within one second of the actual modification time, correct user identifiers matching the session context, entity identifiers matching the modified records, and complete change descriptions capturing both old and new values for modified fields.

Concurrent modification tests verify that no audit log entries are lost when multiple concurrent requests modify the same entities, that all changes are recorded with correct temporal ordering, and that the audit trail accurately represents the sequence of modifications.

Bulk operation tests verify that bulk modifications create individual audit log entries for each affected entity rather than aggregating into single entries.

Session rollback tests verify that rolled-back operations do not create audit log entries, ensuring that the audit trail only contains committed changes.

Error handling tests verify that hook exceptions are properly propagated and do not cause silent failures or data corruption.

Performance tests establish baseline metrics showing that audit logging overhead is under five percent for typical entity create, update, and delete operations, and that overhead does not exceed ten percent even under concurrent load.

The complete hook test suite runs in under one minute when executed in parallel, enabling developers to run full hook validation quickly during development iterations.

All hook tests follow the Arrange-Act-Assert pattern with clear setup, modification, and verification phases. Test names clearly describe what hook behavior is being validated, such as test-after-insert-hook-creates-audit-log-entry-with-correct-operation-type or test-concurrent-modifications-do-not-lose-audit-log-entries.

The test suite generates coverage reports showing which hook code paths are exercised, identifying any untested branches that require additional test cases.
