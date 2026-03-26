---
task: T03
story: S01
epic: EPIC-6
title: Implement notification queue
status: ready
priority: medium
created: 2026-03-25T17:13:26.732723
---

# T03: Implement notification queue

## Description

Implement a durable, database-backed notification queue that decouples notification dispatch from the request-response cycle. When the application needs to send a notification — such as an adoption confirmation email or a donation receipt — it writes a record to the notification queue table rather than calling the email provider inline. A background worker then reads from the queue, attempts delivery, and updates the record with the outcome. This approach prevents slow or failing email deliveries from degrading API response times and provides a complete audit trail of every notification the application has attempted to send.

The queue is implemented entirely within PostgreSQL and FastAPI, with no external queue service or message broker required. For the shelter's expected traffic volume, a database-backed queue is sufficient and avoids the operational complexity of running Redis or a managed queue service.

## Why a Queue Instead of Inline Dispatch

Sending email inline, inside the same FastAPI request handler that processes the triggering action, introduces several problems. If the email provider is slow or temporarily unavailable, the adopter's HTTP response is delayed by the same amount. If the email send fails, the only options are to bubble the error up to the user (confusing, since the adoption was already recorded) or to silently discard it (losing the notification entirely). There is also no audit trail of what was sent, when, and whether it succeeded.

A queue solves all of these: the request handler records the intent to send and returns immediately, the worker handles delivery asynchronously, failed sends are retried automatically up to a configurable limit, and every attempt is logged with its outcome.

## Database Schema

The notification queue is represented by a table named notification_queue in the application database. Alembic manages the migration that creates this table. The table has the following logical structure: a unique identifier per row, a notification type that describes the purpose of the notification (values include adoption_confirmation, adoption_approved, adoption_rejected, donation_receipt, and password_reset), a status field that tracks the row through its lifecycle (values are pending, processing, sent, and failed), a recipient field containing the email address, a subject line, a body stored as HTML, an optional plain-text fallback body, a retry count starting at zero, a field for the last error message from a failed attempt, a created timestamp, a processed timestamp that is null until the notification reaches a terminal state, and two optional reference fields that link the notification back to the entity that triggered it (an entity type string and an entity UUID). A partial index on the status column filtered to rows where status equals pending allows the worker to efficiently query for work without scanning the full table.

Row-level security is enabled on the notification_queue table. No user-facing role has direct access to the table contents. All reads and writes go through the application's service account, which bypasses row-level security checks using SQLAlchemy's connection configured with the service account credentials.

## Enqueue Function

A module at src/notifications/queue.py exposes a single public function named enqueue_notification. This function accepts the notification type, recipient email address, subject, HTML body, optional plain-text body, and optional entity type and entity ID. It creates a SQLAlchemy insert statement that writes a new row with status pending and returns the UUID of the newly created row. The function is called from within request handlers and from within Alembic-triggered application logic. It does not attempt delivery; it only records the intent.

Callers never need to await delivery confirmation. If the insert fails (for example due to a database connection error), the exception propagates to the caller, which handles it the same way as any other database failure.

## Background Worker

The notification worker is a FastAPI startup task registered using the application's lifespan context manager. When the FastAPI application starts up, the lifespan context starts an asyncio background task that runs in a loop. Each iteration of the loop queries the notification_queue table for a batch of rows where status is pending, ordered by created timestamp ascending, limited to a configurable batch size (defaulting to ten). For each row it claims, the worker atomically updates the status to processing before attempting delivery, using a SQL update with a where clause that filters to status equals pending. This optimistic locking pattern prevents a second worker instance from processing the same row if the application is scaled horizontally.

After updating the row to processing, the worker calls the email dispatch function. If the dispatch succeeds, the worker sets the status to sent and records the processed timestamp. If the dispatch fails, the worker increments the retry count and either resets the status to pending (if the retry count is below the configured maximum) or sets the status to failed (if the maximum is reached). In both failure cases, the last error field is updated with the error message from the failed attempt.

After processing the full batch, the worker sleeps for a configurable interval before polling again. The default polling interval is five seconds. A shorter interval reduces notification latency; a longer interval reduces database load. The interval is set via the NOTIFICATION_WORKER_POLL_INTERVAL_SECONDS environment variable.

The worker is designed to be restartable: if the application crashes while a batch is processing, any rows left in status processing will not be retried automatically. An operational runbook at docs/operations/notification-queue-runbook.md describes how to reset stuck processing rows back to pending after investigating the cause of the crash.

## Retry Logic and Dead Letter Handling

The maximum number of delivery attempts is three by default, configurable via the NOTIFICATION_MAX_RETRIES environment variable. Retries use an exponential backoff strategy: the first retry is attempted after the polling interval, the second after double the polling interval, and so on. The actual retry timing is approximate because the worker polls on a fixed schedule rather than per-row; the retry count and timing are sufficient to handle transient email provider outages.

Rows that reach the maximum retry count are set to failed status and are not retried further. Failed rows are not deleted; they remain in the table permanently as part of the audit trail. A separate administrative endpoint, accessible only to admin-role users, allows shelter staff to view failed notifications and manually requeue them if appropriate. Requeuing resets the retry count to zero and the status to pending, allowing the worker to attempt delivery again.

## Notification Log for Audit

In addition to the notification queue (which tracks delivery lifecycle), a separate notification_log table provides a permanent, append-only record of every notification that was successfully sent. When the worker sets a row to sent status, it also inserts a record into notification_log with the notification type, recipient, entity type, entity ID, and sent timestamp. The notification queue rows may eventually be archived or pruned for performance; the notification log is retained indefinitely.

The notification log is what the adoption workflow test and donation workflow test query in their verification stages: they check that a notification_log entry was created for the expected notification type and entity, without caring about the internal queue mechanics.

## Distinguishing Transactional and Batch Notifications

Transactional notifications are those triggered by a specific user action and expected to arrive within seconds: adoption confirmation, adoption approval, and donation receipt. These are enqueued immediately inside the request handler that processes the triggering action. Because the worker polls every five seconds, transactional notifications are typically delivered within ten seconds of the triggering event.

Batch notifications are those sent on a schedule rather than in response to a user action: weekly volunteer schedule reminders and monthly donor impact summaries. These are enqueued by a scheduled task that runs via the FastAPI lifespan background machinery or, in a future phase, by a cron job that calls a staff-only API endpoint. Batch notifications use the same queue and worker infrastructure as transactional notifications; the only difference is what triggers the enqueue call.

## Test Coverage

Unit tests for the enqueue_notification function verify that calling it with valid arguments produces the correct insert statement and returns a UUID. The tests mock the SQLAlchemy session to avoid requiring a real database.

Integration tests for the worker verify the full lifecycle: a test inserts a pending row, starts the worker for one iteration, and asserts that the row transitions to sent and that the mock email dispatch function was called with the correct arguments. A separate integration test verifies the failure path: the mock email dispatch is configured to raise an exception, and the test asserts that the row's retry count is incremented and that the row transitions to failed after the maximum retry count is exceeded.

The integration tests use the same transactional rollback fixture as the rest of the test suite, ensuring no test data persists between tests.
