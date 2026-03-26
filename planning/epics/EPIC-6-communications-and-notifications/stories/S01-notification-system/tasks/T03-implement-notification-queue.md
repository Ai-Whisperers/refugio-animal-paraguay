---
task_id: T03
task_title: "Implement Asynchronous Notification Queue with Background Tasks"
task_status: pending
story_id: S01
epic_id: EPIC-6
created_date: 2026-03-25
estimated_effort: 8 hours
dependencies:
  - "T01-setup-notification-service (email service integration)"
  - "T02-design-notification-templates (Jinja2 template structure)"
  - "EPIC-10 authentication (JWT user context)"
  - "PostgreSQL notifications table schema"
---

## Overview

This task implements an asynchronous notification queue system using FastAPI BackgroundTasks for managing email delivery to users. The notification system must handle adoption request submissions, donation confirmations, and status updates asynchronously, preventing slow email operations from blocking HTTP response cycles. The implementation stores notification records in PostgreSQL for audit trails and retry tracking, while using FastAPI's background task mechanism to queue email dispatch operations without external queue dependencies like Celery or RabbitMQ.

## Why This Task Matters

The Refugio Animal Paraguay platform requires reliable, non-blocking email notifications to keep users informed about adoption progress, donation receipts, and shelter updates. If email operations block the main request thread, API endpoints become slow and unreliable. By implementing background tasks, we ensure that email failures do not cause donation or adoption submission endpoints to fail. Additionally, maintaining notification records in the database allows staff to troubleshoot delivery issues and resend notifications manually when needed. This approach balances simplicity (no external queue broker required) with reliability (persistent audit trail).

## Technical Requirements

The notification queue system must use FastAPI's BackgroundTasks to dispatch email operations asynchronously. Each notification record includes metadata fields: notification_type (adoption_submitted, adoption_approved, donation_received, etc.), recipient_email, subject, template_name, template_context (serialized JSON with donor name, animal name, etc.), status (pending, sent, failed), created_at timestamp, sent_at timestamp, and error_message for failed attempts. Notifications must be created synchronously within a database transaction during the primary request, then dispatched asynchronously to avoid blocking the response. The system must implement exponential backoff retry logic: first retry after 5 minutes, second after 30 minutes, third after 2 hours, with a maximum of 3 retry attempts before marking as permanently failed. Email sending must use the SMTP service configured in environment variables (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD) with TLS encryption. Template rendering must use Jinja2 to populate context variables into email bodies. The notification status field must track progression: pending means not yet attempted, sent means successfully delivered, failed means exhausted retries, retrying means awaiting next retry window. Timestamps must be in UTC using Python's datetime.datetime.utcnow(). The system must not retry notifications marked as failed permanently; permanent failures include invalid email addresses detected by SMTP responses. The service must gracefully handle SMTP connection timeouts (5-second timeout) by logging the error and scheduling automatic retry. Notifications must include X-Refugio-ID headers for tracking and X-Notification-Type headers for filtering. All notification operations must be tested with mocked SMTP connections using unittest.mock.patch.

## Implementation Approach

Begin by creating a new database table schema for notifications with columns: id (UUID primary key), notification_type (string enum), recipient_email (string), subject (string), template_name (string), template_context (JSON), status (string enum with values pending, sent, failed, retrying), created_at (timestamp), sent_at (timestamp nullable), attempted_count (integer defaulting to zero), next_retry_at (timestamp nullable), error_message (string nullable), and user_id (foreign key to users table). Add a database index on status and next_retry_at to efficiently query pending and due-for-retry notifications.

Create a NotificationQueue service class with methods for enqueuing notifications and dispatching them asynchronously. The enqueue method accepts notification_type, recipient_email, subject, template_name, and template_context dictionary, creates a NotificationRecord in the database with status pending, and returns the notification ID. The dispatch_background_task method accepts a notification record ID, retrieves it from the database, renders the Jinja2 template with the stored context, connects to SMTP using a context manager for automatic cleanup, sends the email, records the sent_at timestamp and status sent, and updates attempted_count. If an SMTP exception occurs, the dispatch method catches it, increments attempted_count, logs the error with context (notification ID, email address, error type), calculates next_retry_at based on exponential backoff (5 minutes for first retry, 30 for second, 2 hours for third), and if attempted_count exceeds 3, marks status as failed with the error message.

Integrate background task dispatch into FastAPI endpoints by injecting BackgroundTasks parameter into endpoints for adoption submissions and donations. After creating an adoption request or donation record in the database, call add_task on the BackgroundTasks instance to queue the dispatch operation. Example pattern: background_tasks.add_task(notification_queue.dispatch_background_task, notification_id=created_notification.id). This ensures the HTTP response returns immediately while email dispatch happens asynchronously.

Create a scheduler job (using APScheduler or a simple async task in the startup event) that runs every 30 seconds to check for notifications with status retrying and next_retry_at in the past, then dispatches them. This ensures retries happen automatically without manual intervention.

Implement retry logic that distinguishes between transient failures (network timeouts, SMTP connection errors) which trigger retries, and permanent failures (invalid email syntax, authentication failures, recipient rejection) which do not. Log all retry decisions with structured logging including notification_id, current_attempt, next_retry_time, and reason_for_retry.

## Success Criteria

Notifications are successfully created in the database synchronously within the same transaction as the triggering event (adoption submission or donation creation), with status field set to pending and created_at timestamp recorded. Background task dispatch is triggered immediately without blocking the HTTP response, allowing endpoints to return within 200 milliseconds. Emails are successfully sent to valid recipient addresses within 2 seconds via the SMTP service, with sent_at timestamp recorded and status updated to sent. SMTP failures automatically trigger retry scheduling with exponential backoff: first retry is scheduled 5 minutes after initial failure, second retry 30 minutes after that, third retry 2 hours after second failure. After 3 failed attempts, the notification status changes to failed with error_message populated with the last SMTP error. Invalid email addresses detected by SMTP response codes (5xx rejection codes) are marked as failed immediately without retry. The retry scheduler runs automatically and processes due notifications without manual intervention. Unit tests mock the SMTP connection and verify that email sending succeeds when the mock responds affirmatively, and that retries are scheduled when mock raises SMTPException. Integration tests verify the complete flow: submitting an adoption request triggers notification creation, the background task executes asynchronously, the notification record status updates to sent after successful SMTP delivery. Notifications can be queried by type and status for audit purposes. Staff can manually resend a previously failed notification by creating a new notification record or updating the existing record's status to pending. All notification operations are logged with structured logging including timestamp, notification ID, recipient email, operation type, and result.
