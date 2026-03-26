---
epic: EPIC-9
title: Deployment & Infrastructure
status: ready
created: 2026-03-25T17:13:26.735971
updated: 2026-03-25T17:13:26.735973
---

# EPIC-9: Deployment & Infrastructure

## Overview

**Goal**: Establish the containerization, CI/CD pipeline, hosting environment, and observability stack that allow the platform to be deployed reliably, monitored continuously, and debugged efficiently — from the first staging deployment through ongoing production operations.

**Why it matters**: The platform's features have no value if the application cannot be deployed consistently or if defects in production go undetected for hours. Infrastructure is the difference between a codebase and a running service. For the Refugio Animal Paraguay platform specifically, the hosting decisions have compliance implications: European donors transmit personal and payment data through the platform, which creates GDPR obligations around data residency and secure transmission. The choice of an EU-West region for hosting is not merely a latency optimization; it is a compliance decision. Containerization ensures that the development environment, the CI pipeline, and production all run the same code with the same dependencies, eliminating the class of bugs that only appear on one environment.

**Target users**: Developers who need a reliable local development environment and fast feedback from CI; the shelter administrator who deploys new versions without engineering support; the shelter owner who monitors uptime and receives alerts when the platform is unavailable; Anthropic's operations team (or the hosting provider's support team) who investigate production incidents.

---

## Scope

### In Scope

- Multi-stage Dockerfile for the FastAPI application: a build stage that installs Python dependencies and compiles any native extensions, and a minimal runtime stage that copies only the installed packages and application code, runs as a non-root user, and exposes the health check endpoint; target image size under 200 megabytes
- Docker Compose configuration for local development: defines the API service, a PostgreSQL 16 service, and a Redis service (for optional background task queue); includes volume mounts for hot-reload, environment variable loading from a local file, and health check dependencies between services
- GitHub Actions CI/CD pipeline: triggers on push and pull request to all branches; runs lint, type check, and unit tests on every push; runs the full test suite including integration tests on pull requests targeting develop or main; builds and pushes a Docker image on merge to main; deploys to the target hosting environment on release tag creation
- Hosting environment provisioning: documents the evaluated hosting options and the selected provider; configures the production PostgreSQL managed database service; configures environment variable injection; sets up the custom domain with DNS records pointing to the hosting provider
- TLS certificate provisioning via Let's Encrypt with automatic renewal; enforces HTTPS-only by redirecting HTTP requests to HTTPS; sets the HSTS header with a long max-age; configures minimum TLS 1.2
- CDN configuration for static assets served by the frontend (TBD); configures appropriate cache-control headers on public API endpoints (the animal catalog and animal detail endpoints) to allow edge caching without serving stale adoption status data
- Sentry ASGI middleware integration for error capture and performance tracing; configures release tracking so that errors are associated with the deployed version; configures PII scrubbing via the before_send callback to exclude donor email addresses, adopter names, and payment identifiers from Sentry event payloads
- Structured logging with the structlog library using JSON output in production and staging environments and a human-readable console format in development; establishes the standard log fields (request ID, user ID, duration, HTTP status code) and the explicit exclusion list (passwords, JWT tokens, personal data); propagates a per-request correlation ID via Python context variables so that all log lines from a single request share a common identifier
- External uptime monitoring via UptimeRobot or equivalent: three monitors covering the health check endpoint, a representative public API endpoint (animal listing), and the TLS certificate expiry date; alert notifications go to the shelter owner's email and optionally to a designated phone number
- GET /health endpoint: returns HTTP 200 with a JSON body containing the application status, current timestamp, database connectivity status (verified by a lightweight query), and the deployed version string; returns HTTP 503 when the database is unreachable; sets Cache-Control to no-store so that monitoring tools always hit the application rather than a cached response

### Out of Scope

- Kubernetes or container orchestration (the expected traffic volume does not justify this complexity; a single container instance on a managed hosting platform is appropriate for the shelter's scale)
- Blue-green or canary deployment strategies (straightforward rolling deployment with a smoke test is sufficient for this scale)
- Database backup automation (this is provided by the managed PostgreSQL service's built-in backup retention; no custom backup tooling is needed)
- Infrastructure as code beyond Docker and docker-compose (Terraform or Pulumi may be introduced in a future phase if infrastructure complexity grows)
- Self-hosted email server (the platform uses a third-party transactional email provider)

---

## Stories

- **S01: Docker & Container Setup** — Write the multi-stage Dockerfile following the layering strategy that maximizes cache reuse: copy and install the requirements file before copying application code so that dependency installation is cached unless requirements change. Write the docker-compose.yml with the three services and their dependency ordering. Write the .dockerignore file excluding test directories, documentation, virtual environment directories, and the git history. Write the docker-compose.override.yml for development-specific settings that should not be committed as defaults. Verify that the final runtime image runs as a non-root user and that the application starts cleanly with the environment variables defined in the example environment file.

- **S02: CI/CD Pipeline** — Write the GitHub Actions workflow file that defines the test job (lint with ruff, type check with mypy, format check with black, unit tests with pytest) and the integration test job (full test suite with a PostgreSQL service container, coverage report upload). Write the deployment job that triggers on merge to main or on a release tag, builds the Docker image, pushes it to the container registry, and deploys to the hosting provider using the provider's deployment API or CLI. Write the linting job that uses reviewdog to annotate pull requests with inline comments for lint violations. Configure the pipeline to cache pip dependencies between runs to reduce execution time.

- **S03: Production Deployment** — Document the hosting provider selection decision, including the evaluated alternatives and the reasons for the final choice, with particular attention to EU-West region availability for GDPR data residency, managed PostgreSQL availability, and pricing at the expected traffic volume. Configure the production environment: domain registration, DNS records, TLS certificate, environment variable secrets in the hosting provider's secret management system. Write the deployment runbook documenting the step-by-step process for deploying a new release, rolling back to a previous version, and responding to a failed deployment. Configure the CDN for static assets with appropriate cache lifetimes.

- **S04: Monitoring & Logging** — Integrate the Sentry ASGI middleware into the FastAPI application startup; configure the Sentry DSN, environment tag, and release string from environment variables; implement the PII scrubbing callback that removes personally identifiable fields before events are sent to Sentry. Implement the structlog configuration module that selects JSON rendering for production and staging environments; define the standard log fields as a processor chain; implement the RequestIdMiddleware that generates a UUID4 per request, stores it in a Python context variable, and includes it in both the response header and every log line produced during that request's lifetime. Configure UptimeRobot with the three-monitor setup and the alerting contacts. Implement the GET /health endpoint with the database connectivity check and the cache-control header.

---

## Dependencies

**Depends on**:
- All feature epics (EPIC-1 through EPIC-8) — the CI/CD pipeline tests and deploys the features built in those epics; this epic provides the infrastructure that makes deployment possible, but it depends on there being application code to containerize and test
- Third-party accounts: GitHub (repository and Actions), a container registry (GitHub Container Registry or Docker Hub), the selected hosting provider, Sentry, UptimeRobot, and the domain registrar

**Blocks**:
- Nothing technically; however, the CI/CD pipeline defined in S02 is a hard dependency for the project's development velocity — without it, each developer manually verifies quality before merging, which is slower and less reliable

---

## Success Metrics

- The CI/CD pipeline completes a full test run and deploys a new version to the staging environment in under ten minutes from the time a commit is pushed to the develop branch
- The Docker image build completes in under three minutes when application code has changed but dependencies have not changed, demonstrating effective layer caching
- The GET /health endpoint returns a 200 response with a database connectivity confirmation in under 50 milliseconds
- UptimeRobot sends an alert within five minutes of the production health check endpoint returning a non-200 response
- Zero production deployments with high or critical security findings, enforced by the security scan stage blocking the deployment job when findings are detected
- The structured logs for any single API request contain a shared request ID that allows all log lines for that request to be retrieved with a single filter query

---

## Risk Factors

- **EU data residency requirements**: GDPR requires that personal data of EU residents not be transferred to third countries without appropriate safeguards. If the hosting provider's EU-West region processes data in a jurisdiction outside the EU, this creates compliance exposure. Mitigation: verify during hosting provider selection that the EU-West region processes and stores all data within the European Economic Area; document this in the platform's data processing record.
- **Sentry PII leakage**: Sentry's error capture will include request context, which may contain personal data in query parameters, request bodies, or local variable values. Mitigation: the before_send callback must explicitly strip or hash any field matching a known PII pattern; this scrubbing must be tested with an integration test that verifies no personal data appears in a captured test event.
- **Cold start latency on low-traffic hosting plans**: Some managed hosting providers shut down container instances after periods of inactivity and restart them on the next request, causing a noticeable delay for the first request after a quiet period. Mitigation: select a hosting plan that keeps at least one instance running at all times, or configure a scheduled health check that prevents the instance from going idle.
- **Dependency on third-party CI minutes**: GitHub Actions provides a limited number of free CI minutes per month for private repositories. A poorly optimized pipeline that does not cache dependencies could consume this budget quickly. Mitigation: implement pip dependency caching in the workflow file from the outset; monitor CI minute consumption monthly; consider self-hosted runners if costs become significant.
- **Paraguay latency for local users**: The EU-West hosting region optimizes for the Dutch owner's primary stakeholder network but adds latency for local Paraguayan users (adopters, volunteers, local donors) who are geographically distant from EU-West data centers. Mitigation: evaluate whether a CDN with a South American edge node can serve the public API responses (animal catalog, animal detail) with acceptable latency for local users; document the latency trade-off and revisit if the Paraguayan user base grows significantly.

---

## Effort & Priority

**Priority**: Cross-cutting and foundational. The Docker and docker-compose setup (S01) should be done at project start to ensure all developers use the same environment. The CI/CD pipeline (S02) should be configured as soon as the first feature is deployable. Hosting and monitoring (S03, S04) must be in place before the platform goes live with real users or real payment data.

**Estimated effort**: Two sprints. Docker setup and CI/CD pipeline configuration (S01, S02) form the first sprint, ideally started before the first feature epic is in progress. Hosting provisioning, TLS, monitoring, and logging (S03, S04) form the second sprint, timed to coincide with the platform approaching its first production deployment.
