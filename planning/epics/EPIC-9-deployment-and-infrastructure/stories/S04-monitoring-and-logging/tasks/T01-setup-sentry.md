---
task: T01
story: S04
epic: EPIC-9
title: Setup Sentry
status: ready
priority: medium
created: 2026-03-25T17:13:26.737105
---

# T01: Setup Sentry

## Description

Integrate Sentry into the FastAPI application for error tracking, performance tracing, and release monitoring. The integration must capture unhandled exceptions and performance degradations in production and staging, while respecting GDPR requirements by scrubbing personal data before it leaves the application. Sentry provides a centralized view of application health that complements the infrastructure-level monitoring configured in T03.

## Why Sentry

Application errors that do not result in complete downtime — a broken adoption form, a failed donation webhook, a corrupt pagination response — are invisible to infrastructure monitoring tools like uptime checkers or server metrics dashboards. Sentry captures these failures at the application layer and provides the stack trace, request context, and frequency data needed to diagnose and prioritize them. For a small team without dedicated oncall engineers, Sentry's ability to group similar errors, suppress noise from known issues, and send targeted alerts makes it the most practical error observability tool available.

Sentry's performance tracing feature records the duration of every incoming request and breaks it down into its component spans: database query time, external HTTP calls, and application processing time. This is the primary mechanism for identifying slow endpoints before they affect donor experience, and for validating that performance regressions introduced by new code are caught in staging before reaching production.

## SDK Integration

The Sentry Python SDK is added as a project dependency. It is initialized in the FastAPI application's lifespan function, which ensures that the Sentry client is configured before any request handling begins and is properly shut down when the application terminates. Initialization happens inside the lifespan context, not at module import time, because module-level initialization makes it impossible to suppress Sentry during test runs without patching global state.

The Sentry SDK integrates with FastAPI through the SentryAsgiMiddleware class, which wraps the ASGI application. This middleware intercepts each request and response, creates a Sentry transaction for each request, and reports unhandled exceptions. The middleware is applied last in the middleware stack so that it wraps all other middleware and captures exceptions that bubble up through any layer.

## GDPR-Compliant PII Scrubbing

Sentry events must never contain personal data about donors or adopters. The SDK's before_send callback is used to intercept every error event before it is transmitted, and the before_send_transaction callback intercepts every performance event. These callbacks inspect the event payload and remove or redact known PII fields before the event leaves the application.

The fields scrubbed in the before_send callback include: the email address from any request body or URL parameter, any field named full_name, first_name, last_name, phone, or address, the Authorization header and its contents, any field matching the pattern of a Stripe API key or payment token, and the donor_id and adopter_id values in the request body. These values are replaced with the literal string REDACTED rather than removed entirely, so that the event structure remains parseable and the presence of sensitive fields is still visible without their values.

The before_send callback also strips the user object from Sentry events, which Sentry normally populates automatically from session or request context. Donor email addresses must not appear in Sentry's user identification fields.

The Sentry DSN (data source name, the URL that identifies the Sentry project) is stored as an environment variable named SENTRY_DSN. This value is not sensitive in the same way as API keys — anyone with the DSN can send events to the project but not read them — but it is still excluded from committed code and version control following the project's general secrets management policy.

## Environment Tagging

Each Sentry event is tagged with the environment it originated from. The ENVIRONMENT environment variable (set to production, staging, or development in each deployment environment) is passed to the Sentry SDK's environment parameter at initialization time. This allows events from staging deployments to be filtered out of production alert rules while still being captured and visible in the Sentry dashboard for debugging pre-production issues.

In the development environment, Sentry is disabled entirely. The Sentry SDK's init function is called only when the ENVIRONMENT variable is set to production or staging, and the SENTRY_DSN variable is present. If either condition is absent, the application initializes without Sentry and all Sentry API calls become no-ops. This prevents test noise, avoids rate-limiting the Sentry project with development events, and means that local development works without a Sentry account.

## Release Tracking

The Sentry SDK is configured with the application's release version, derived from the Git commit SHA at build time. The GitHub Actions build pipeline records the current commit SHA into an environment variable that the container reads at startup and passes to Sentry. Sentry uses the release value to associate errors with specific deployments, which enables the "regression" detection feature: Sentry can identify when an error that was previously resolved reappears in a new release.

The Sentry release also integrates with source maps and stack trace linking. When the application raises an exception, Sentry can display the exact line of source code responsible, linked to the commit on GitHub. This requires that the Sentry project is configured with the GitHub repository integration, which maps release versions to commits.

## Performance Tracing Configuration

The Sentry SDK's traces_sample_rate parameter controls what fraction of requests are traced for performance monitoring. In production, the sample rate is set to 0.1, meaning one in ten requests generates a full performance trace. This rate is sufficient to detect latency regressions while keeping Sentry's event volume and storage cost proportional to a small shelter platform's budget. In staging, the sample rate is set to 1.0 so that every request during pre-deployment testing generates a trace, giving complete visibility into endpoint performance before a change reaches production.

The traces_sampler function, rather than a fixed rate, is used to apply differential sampling: the GET /health endpoint is excluded from tracing entirely because it is called every thirty seconds by the uptime monitor and would otherwise generate the majority of performance traces while providing no diagnostic value. The donation and payment intent endpoints are always sampled (rate 1.0) regardless of the global sample rate, because their performance is business-critical and every transaction should be visible.

## Alert Rules

Two Sentry alert rules are configured for the production environment. The first rule fires when the count of new errors (errors not previously seen in this release) exceeds five in a ten-minute window. This threshold is deliberately low because this application is not high-traffic; five new distinct errors in ten minutes indicates a meaningful problem rather than routine background noise. The alert is delivered to the shelter owner's email address.

The second rule monitors performance degradation. It fires when the p95 response time for any transaction exceeds one second, measured over a fifteen-minute window. The p95 threshold of one second is conservative relative to the performance budgets defined in EPIC-8 S04, but Sentry's aggregation latency means short-lived spikes may not appear immediately; a one-second p95 sustained for fifteen minutes represents a clear user experience problem. This alert also goes to the shelter owner's email.

Both alert rules are suppressed for the staging environment to avoid false alarms during routine deployment testing. A separate, lower-priority alert rule for staging fires only when error counts exceed fifty, acting as a safety net for catastrophic staging failures without generating alert fatigue.

## Testing the Integration

The integration is verified in staging before production deployment by triggering a deliberate error through a test-only endpoint that raises an unhandled exception. The resulting Sentry event is inspected to confirm that the environment tag is correct, the release version matches the deployed commit, the before_send scrubbing removed the email field from the simulated request body, and the event appeared within sixty seconds of the error occurring.

## Acceptance Criteria

- Sentry SDK initialized in the FastAPI lifespan function, not at module import time
- SentryAsgiMiddleware wraps the ASGI application and captures unhandled exceptions
- before_send callback scrubs email, name, address, token, and Authorization header fields
- before_send sets user object to null before transmission
- ENVIRONMENT variable controls Sentry activation (disabled in development)
- Release version passed to Sentry from build-time Git SHA
- traces_sample_rate is 0.1 in production, 1.0 in staging
- GET /health excluded from performance traces
- Donation endpoints always sampled
- Alert rule for new errors exceeding 5 per 10 minutes in production
- Alert rule for p95 exceeding 1 second over 15 minutes in production
- Integration verified in staging with deliberate error and event inspection
