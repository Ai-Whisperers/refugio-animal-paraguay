---
task: T01
story: S04
epic: EPIC-8
title: Setup performance monitoring
status: ready
priority: medium
created: 2026-03-25T17:13:26.735818
---

# T01: Setup performance monitoring

## Description

Establish a performance testing and monitoring framework for the FastAPI application. This task covers load testing strategy using Locust, defining performance budgets for each endpoint category, profiling slow code paths with py-spy, and integrating Sentry performance tracing into the application's request lifecycle. The goal is to surface performance regressions before they reach production and to give the development team clear, measurable targets to work toward.

## Performance Budgets

Performance budgets define the maximum acceptable response time at the 95th percentile for each category of endpoint. The thresholds are chosen based on the expected user population and the nature of each operation. Budgets are enforced in the load testing suite; any test run that produces p95 latency above the budget for a given category is treated as a failure.

The public animal listing and animal detail endpoints serve anonymous visitors who are browsing available animals for adoption. These must respond at the 95th percentile within two hundred milliseconds. Donors visiting the donation landing page and submitting a payment intent creation request must receive a response within five hundred milliseconds at the 95th percentile, since payment flows are sensitive to perceived slowness. Staff-facing admin report endpoints aggregate data across the full records history and are permitted up to three seconds at the 95th percentile, because staff users understand that reporting queries are more expensive and are not expecting sub-second responses. Authentication endpoints including login and token refresh must respond within three hundred milliseconds at the 95th percentile.

These budgets are documented in a file named performance-budgets.md located at the root of the tests directory, so that any team member can consult the current targets without reading test code.

## Locust Load Test Structure

Locust is the chosen load testing tool. It is installed as a development dependency. Load test files live under tests/performance/, with one file per user behavior scenario.

The animal browse scenario simulates a visitor who lands on the public animal listing endpoint, paginates through multiple pages of results, and then visits the detail page for one specific animal. This scenario uses no authentication token and exercises the read-heavy, public-facing path. The scenario is defined as a Locust task set with relative weights assigned to each step, reflecting the expected distribution of traffic: listing pages receive approximately four times the traffic of individual detail pages.

The donation scenario simulates a donor who submits a payment intent creation request with a EUR amount and then polls the donation status endpoint until the response reflects the expected pending state. Since this scenario depends on Stripe test mode, the Locust scenario uses the Stripe test API keys loaded from environment variables. The scenario does not simulate the Stripe redirect or the webhook delivery, since those are outside the application's control in a load test context.

The authentication scenario simulates a staff user who logs in, makes several API calls that require the staff JWT token, and then lets the token expire before refreshing. This scenario is run at a lower concurrency level than the public scenarios because staff users represent a small fraction of total traffic.

Each scenario is run with a staged ramp-up: Locust starts with one concurrent user, increases to the target concurrency level over a period of sixty seconds, holds at that level for five minutes, then ramps back down. The ramp-up period prevents a thundering herd at test start and makes the results more representative of real traffic growth.

Load test results are written to a JSON file that records per-endpoint statistics including request count, median, 95th percentile, 99th percentile, maximum, and failure count. A separate Python script reads this JSON file, compares each endpoint against the corresponding budget, and exits with a non-zero code if any budget is exceeded. This script is called from the GitHub Actions performance pipeline job.

## Database Query Profiling

Slow database queries are the most common source of performance regressions. The SQLAlchemy engine is configured in development and staging environments with a query timing middleware that logs any query taking longer than fifty milliseconds. The log entry includes the SQL text (with bound parameters masked), the duration, and the request ID so that slow queries can be traced back to the HTTP request that triggered them.

The SQLAlchemy before_cursor_execute and after_cursor_execute events are used to implement this timing. The event listeners are registered during application startup when the PROFILE_SLOW_QUERIES environment variable is set to a truthy value. They are not registered in production unless explicitly enabled, to avoid the overhead of timing every query.

The target for any single database query on the hot path (public animal listing, donation status check, adoption request submission) is one hundred milliseconds at the 95th percentile. Any query that regularly exceeds this threshold is a candidate for index addition, query restructuring, or result caching.

## py-spy Profiling

When a specific endpoint or code path is suspected of being slow but query profiling alone does not identify the bottleneck, py-spy is used for CPU profiling. py-spy attaches to the running FastAPI process by its process ID and samples the call stack at a configurable frequency. It produces a flamegraph in SVG format that shows which functions consume the most CPU time.

The profiling workflow is: identify the slow endpoint from Locust results or Sentry traces, generate a representative load for that endpoint using a targeted Locust scenario, attach py-spy to the FastAPI process, and let it sample for sixty seconds. The resulting flamegraph is saved to docs/profiling/ with a filename that includes the endpoint path and the date. Findings from profiling sessions are documented in the same directory as markdown files describing what was found and what change was made in response.

## Sentry Performance Tracing

Sentry's Python SDK is added to the application dependencies. The SentryAsgiMiddleware is wrapped around the FastAPI application instance during startup when the SENTRY_DSN environment variable is present. This middleware automatically creates a transaction for every incoming HTTP request and records its duration, HTTP method, path, and response status.

The traces_sample_rate is set to zero point one in staging, meaning ten percent of all requests are traced. In production it is set to zero point zero five, meaning five percent. These rates provide enough data for statistical analysis without adding significant overhead or Sentry quota consumption. The rate can be overridden with the SENTRY_TRACES_SAMPLE_RATE environment variable for specific performance investigations.

Custom spans are added within the code for operations that are not automatically instrumented. The Stripe payment intent creation call is wrapped in a Sentry span with the description "stripe.payment_intents.create" so that the external API latency is visible separately from the total request duration. Similarly, the email dispatch call is wrapped in a span with description "email.send" to distinguish email sending time from request processing time.

The Sentry SDK is configured to strip personally identifiable information from traces before they are sent. The before_send_transaction callback removes the Authorization header, any query parameter or JSON body field named email, donor_name, or message, and any URL path segments that look like UUID4 values (replacing them with the string stripped-uuid). This ensures that donor names and email addresses never appear in Sentry transaction data.

## Performance Regression Detection in CI

The GitHub Actions pipeline includes a performance job that runs after the test job passes. This job starts the FastAPI application against a test PostgreSQL database seeded with a realistic dataset (five hundred animal records, one thousand adoption requests, two thousand donation records), runs the Locust load test scenarios in headless mode for sixty seconds each at low concurrency (ten users), compares the results against the performance budgets, and fails the pipeline if any budget is exceeded.

The realistic seed dataset is generated by a script at tests/performance/seed_performance_db.py that uses the Faker library to create records with realistic distributions: animal species, adoption request statuses, donation amounts in both EUR and PYG, and timestamps spread across the past two years.

The performance job is not run on every push to feature branches, only on pushes to develop and on pull requests targeting develop. This keeps CI time manageable for routine development while still catching regressions before they merge to the integration branch.
