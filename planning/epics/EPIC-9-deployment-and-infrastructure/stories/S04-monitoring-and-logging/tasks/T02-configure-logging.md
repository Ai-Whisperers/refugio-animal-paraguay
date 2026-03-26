---
task: T02
story: S04
epic: EPIC-9
title: Configure logging
status: ready
priority: medium
created: 2026-03-25T17:13:26.737162
---

# T02: Configure Logging

## Description

Configure structured, machine-parseable logging for the FastAPI application using a consistent format that enables operational visibility without exposing personal data. Every log entry must carry a correlation identifier so that a complete request trace can be reconstructed from the log stream. The logging configuration must define clear policies about what information is included at each log level, enforce PII exclusion across all log outputs, and produce output in a format compatible with centralized log aggregation services.

## Why Structured Logging

Plain-text log lines are easy for humans to read in a terminal but are difficult for machines to parse, filter, and aggregate. When the application runs in a containerized deployment behind a reverse proxy and produces hundreds of log lines per minute, operators need to search for all events related to a specific request, filter by log level, or count errors by endpoint. Structured logging — where each log entry is a JSON object with consistent field names — makes these operations trivial for any log aggregation service. The cost is a slightly less readable raw terminal output, which is outweighed by the operational benefit in all non-development contexts.

The structlog library is preferred over Python's built-in logging module for this application because it has first-class support for the processor pipeline pattern, where log records pass through a sequence of transformations before output. This makes it straightforward to add the request correlation ID, redact PII fields, and format the output differently per environment without conditional logic scattered through the application.

## Log Format

In production and staging environments, every log entry is emitted as a single line of JSON. Each JSON object contains at minimum: the timestamp in ISO 8601 format with UTC timezone, the log level as a string, the message, the logger name identifying which module produced the entry, and the request correlation ID when the log entry occurs within a request context. Additional fields are included as the situation requires — a database query log entry includes the query duration; an HTTP response log entry includes the status code and response time; an error log entry includes the exception type and a truncated stack trace.

In the development environment, structlog is configured with a console renderer that produces human-readable colored output with aligned columns. This is purely a developer experience choice: the production JSON processor pipeline is fully active in staging so that log format issues are caught before production deployment.

## Request Correlation IDs

Every HTTP request that the FastAPI application handles is assigned a unique correlation ID, implemented as a UUID4 value. A custom FastAPI middleware named RequestIdMiddleware inspects the incoming request for an X-Request-ID header. If the header is present, its value is used as the correlation ID, allowing external systems such as Cloudflare or Traefik to propagate a correlation ID they assigned. If no header is present, the middleware generates a new UUID4 value. The correlation ID is stored in a Python context variable for the duration of the request.

The structlog processor pipeline includes a processor that reads the correlation ID from the context variable and injects it into every log record produced during that request. This means that every log entry — whether produced in the route handler, a service function, or a SQLAlchemy event listener — automatically carries the same request_id field without any explicit passing of the ID through function arguments. At the end of request processing, the RequestIdMiddleware adds the correlation ID as an X-Request-ID header on the response, so that callers — including the mobile frontend and external webhook senders — can log the correlation ID on their end and use it to match their records with the application's log entries.

## What to Log

The access log records every HTTP request and response at the INFO level. Each entry includes the HTTP method, the path (without query parameters when the path contains resource identifiers that could be PII), the response status code, the response time in milliseconds, the client IP address as presented by Traefik after removing the real visitor IP from the Cloudflare forwarded headers, and the correlation ID. The User-Agent header is not logged because it has limited operational value and can contribute to fingerprinting data.

Application events that represent significant state transitions are logged at INFO: a new adoption request submitted, a donation payment confirmed, an animal record updated, a user account created. These entries include the resource type and a pseudonymous identifier (the UUID primary key, not the name or email of the user involved) so that a specific event can be found in the logs using a known record ID without the log entry itself disclosing PII.

Warnings are logged for conditions that indicate a potential problem but not an immediate failure: a payment webhook arriving with an unexpected event type, an adoption request submitted for an animal that is already marked reserved, a configuration value missing that has a safe default. Warnings require investigation but not immediate action.

Errors are logged for unhandled exceptions, failed external service calls (Stripe API errors, email delivery failures), and database constraint violations that indicate an inconsistent application state. Error log entries include the exception class, the exception message, and a single-level stack trace pointing to the location where the error was caught. Full tracebacks are not included in the structured log because they are large, difficult to parse, and already captured by Sentry (T01) with better tooling for analysis.

## What Not to Log

The following information must never appear in any log entry at any log level: email addresses, full names, street addresses, phone numbers, bank account numbers or IBAN values, Stripe customer IDs or payment method IDs, JWT token values, password hashes or any password-related strings, any cookie value, and the content of POST request bodies containing donor or adopter data. The presence of these field names in a log entry is also discouraged even with redacted values, because log consumers may misinterpret a REDACTED value as a valid identifier.

These restrictions are not merely a privacy best practice — they are required by GDPR Article 5(1)(f), which mandates appropriate technical measures to protect personal data from unauthorized access. Log streams often receive less access control than production databases, and centralized log aggregation services may retain logs for months. A log entry containing a donor's email address and donation amount is a data record subject to GDPR right-of-access and right-of-erasure requests, which cannot be fulfilled for log entries as easily as for database records.

A structlog processor that runs before the output processor inspects each log record's fields and raises an alert if any field value matches patterns associated with known PII types (email-shaped strings, IBAN prefixes, Stripe ID prefixes). This processor acts as a safety net during development and testing; it logs a warning when a potential PII field is detected so that the offending log statement can be found and corrected.

## Log Levels Per Environment

In the development environment, the log level is set to DEBUG, which includes verbose diagnostic output from SQLAlchemy's query logging (query text without bound parameters), from the Alembic migration runner, and from the FastAPI request lifecycle. This level is appropriate for development but would produce an unmanageable volume in production.

In the staging environment, the log level is set to INFO. SQLAlchemy query logging is disabled. Structlog's filter processor drops DEBUG-level entries before they reach the output renderer.

In the production environment, the log level is also set to INFO. The logging configuration is identical to staging because staging's purpose is to validate production behavior. The difference between environments is controlled by the ENVIRONMENT variable, not by separate configuration files.

## Centralized Log Shipping

The application container writes logs to standard output only. It does not write to files, does not manage log rotation, and does not maintain any log storage itself. The container orchestration layer (Docker on Hetzner) captures the standard output stream. An external log shipping agent — the specific service is to be selected based on cost and simplicity when the hosting environment is finalized — reads the container's log output and forwards it to a centralized log aggregation service.

Candidate log aggregation services for this deployment scale include Grafana Loki (self-hosted alongside the application, lowest cost), Logtail by Better Stack (managed service with a generous free tier), and Axiom (managed service optimized for structured JSON logs). The selection is deferred to the hosting finalization phase. The application's logging configuration is designed to be agnostic to the aggregation service: as long as the service can ingest newline-delimited JSON from a container log stream, it will work without application code changes.

## Testing the Logging Configuration

The structlog configuration is exercised in the integration test suite by verifying that a known request produces a log entry with the expected fields. Tests inject a fixed correlation ID into the test request headers and assert that the same ID appears in the captured log output. Tests also verify that a simulated request containing donor email data in the request body does not produce any log entry containing that email value, confirming that the PII detection processor is active.

## Acceptance Criteria

- structlog configured with JSON output in production and staging environments
- Console renderer used in development environment for readability
- RequestIdMiddleware assigns UUID4 correlation ID per request
- X-Request-ID header accepted from upstream and propagated to response
- Correlation ID injected into every log record within the request context
- Access log entries include method, path, status code, duration, and correlation ID
- Application event entries include resource type and UUID identifier, never PII
- Email, name, address, payment, and token values never appear in log output
- PII detection processor warns when suspicious field values are detected
- Log level is DEBUG in development, INFO in staging and production
- Application logs to standard output only, no file management
- Integration tests verify correlation ID propagation and PII exclusion
