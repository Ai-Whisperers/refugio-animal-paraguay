---
task: T03
story: S04
epic: EPIC-9
title: Setup monitoring alerts
status: ready
priority: medium
created: 2026-03-25T17:13:26.737218
---

# T03: Setup Monitoring Alerts

## Description

Configure external uptime monitoring and alerting for the production application so that outages and degraded performance are detected and communicated to the shelter owner before donors or staff discover them independently. This task covers the health check endpoint contract, uptime monitoring configuration, alert threshold definitions, and the on-call runbook that guides the shelter owner through diagnosing and recovering from common failure scenarios.

## Why External Monitoring Matters

Infrastructure-level metrics (CPU, memory, disk) and application-level error tracking (Sentry, T01) both provide valuable signals, but neither tells you definitively that the application is reachable from the public internet. A monitoring service running from an external network performs end-to-end synthetic checks: it makes real HTTP requests to the application's public URL, measures the response time, and verifies the response body. If Cloudflare's routing is misconfigured, if Traefik's TLS certificate has expired, or if the FastAPI application is running but returning 500 errors due to a broken database connection, an external monitor will detect all of these scenarios immediately, while server metrics might show that the machine is healthy.

For a shelter with Dutch donors who cannot complete a donation when the application is down, every minute of undetected downtime represents potential lost funding. An external monitoring service that checks every minute and sends an SMS or email when the check fails gives the shelter owner actionable information within two minutes of an outage beginning.

## Health Check Endpoint Contract

The FastAPI application exposes a GET /health endpoint that serves as the primary target for monitoring checks. This endpoint is not behind JWT authentication — it must be accessible without credentials so that monitoring services can call it without managing tokens. However, it does not return any business data; its response body describes only the operational state of the application's dependencies.

A healthy response returns HTTP status code 200 with a JSON body containing: a status field set to the string "healthy", a timestamp field with the current UTC time in ISO 8601 format, a database field whose value is "connected" when a test query against the PostgreSQL database succeeds, and a version field with the application's release version string. The response also includes a Cache-Control header of no-store so that Cloudflare does not cache it and every monitoring check reaches the origin server.

An unhealthy response returns HTTP status code 503 with a JSON body where the status field is set to "unhealthy" and the database field reflects the specific failure ("connection_refused", "timeout", or "query_failed"). Returning 503 rather than 500 is important because some monitoring services distinguish between application errors (5xx) and service-unavailable conditions (503), and 503 correctly communicates that the service is temporarily unable to handle requests rather than that it crashed.

The health check endpoint performs a lightweight database connectivity test: it issues a single SELECT 1 query against the PostgreSQL connection pool and records whether it succeeds within two hundred milliseconds. It does not run a full application query, does not check external services like Stripe, and does not measure queue depths. The purpose is to confirm that the application can reach its primary data store; more detailed diagnostics are the job of Sentry and the application logs.

## Uptime Monitoring Configuration

UptimeRobot is the selected external monitoring service. It offers a generous free tier that supports up to fifty monitors with five-minute check intervals, and paid plans that allow one-minute intervals. For the initial launch, the free tier with five-minute intervals is sufficient; the one-minute plan can be activated once the shelter is handling live donations.

Three monitors are configured in UptimeRobot. The first monitor targets the GET /health endpoint and expects a 200 response. This is the primary availability check. The second monitor targets the GET /animals endpoint (the public animal listing) and expects a 200 response with a non-empty JSON body. This confirms that the full request path — Cloudflare CDN, Traefik, FastAPI, PostgreSQL — is functioning end to end. The third monitor uses UptimeRobot's SSL certificate expiry check on the production domain and alerts when the certificate will expire within fourteen days, providing a belt-and-suspenders check against Traefik's automatic renewal failing silently.

UptimeRobot is configured to alert after two consecutive failed checks before sending a notification. This prevents a single transient network hiccup (which happens occasionally with any cloud infrastructure) from triggering a false alarm at 3 AM. Two consecutive failures — ten minutes at five-minute intervals — is a reliable signal that something is genuinely wrong.

## Alert Channels

Alert notifications are sent to the shelter owner via email, which is the lowest-friction channel that requires no additional service setup. The UptimeRobot account uses the shelter owner's email address as the primary contact. For higher-urgency scenarios where email response latency is unacceptable — such as a donation processing outage during a fundraising campaign — the owner can enable UptimeRobot's SMS alerting, which costs a small additional fee per message and is documented as an optional upgrade in the runbook.

Slack integration is also configured as a secondary channel, routing alerts to a private Slack channel accessible to anyone with administrative access to the platform. This provides a persistent, searchable log of all uptime events separate from email, which is useful when investigating whether an intermittent issue was a one-off or a recurring pattern.

## Latency Alerting Thresholds

UptimeRobot records response times for each check. A separate alert rule fires when the GET /health endpoint's response time exceeds two seconds for three consecutive checks. Two seconds is well above the normal response time for a health check — which should complete in under two hundred milliseconds on a healthy system — so this threshold will not produce false positives from routine load, but will detect situations where the database is under stress or the application is in a degraded state that has not yet caused complete failures.

Response time data from UptimeRobot is reviewed weekly as part of routine platform maintenance. Persistent elevation of response times above five hundred milliseconds, even without triggering an alert, is a signal to investigate database query plans, connection pool configuration, or application code performance before the degradation becomes severe enough to cause outages.

## Error Rate Alerting

UptimeRobot's alerting is binary: the check either passes or fails. Error rate monitoring — the fraction of requests that return 5xx responses — requires application-level visibility. Sentry's alert rule for error frequency (configured in T01) provides this. The combination of UptimeRobot for availability (is the service reachable at all?) and Sentry for error rate (what fraction of requests are failing?) covers both detection scenarios without redundancy.

If the shelter later adds Grafana for infrastructure dashboards, an error rate panel can be derived from Traefik's access log metrics and a dedicated alert rule added there. For the initial launch, Sentry's error alert rules are sufficient.

## On-Call Runbook

The runbook at docs/operations/oncall-runbook.md documents the diagnostic procedure the shelter owner follows when an alert fires. The runbook is written for a non-engineer: it describes what each alert means in plain language, lists the three most common causes in order of likelihood, and provides step-by-step instructions for each recovery action.

The runbook covers the following scenarios. When the health check fails and the server is unreachable: check Hetzner's status page for datacenter incidents, verify the Cloudflare DNS is resolving to the correct floating IP, confirm the application container is running by logging into the Hetzner server and checking container status. When the health check fails but the server is reachable: check the application container logs for startup errors, verify the database container is running, and if the database container has crashed, follow the database restart procedure documented in docs/operations/database-restore-runbook.md. When the SSL certificate alert fires: check the acme.json file's certificate expiry date, and if Traefik failed to renew, follow the manual certificate renewal procedure. When the Slack alert fires but email did not arrive: check the email spam folder and add UptimeRobot's sender domain to the allowlist.

The runbook also documents the escalation path: if the shelter owner cannot resolve an incident within thirty minutes using the runbook, the contact information for the technical team responsible for the platform is listed with the expected response time.

## Status Page

UptimeRobot provides a public status page at a subdomain of the shelter's domain (for example, status.rafugioanimalpy.com) showing the uptime history for all configured monitors. This page is configured as a public-facing communication tool for donors and staff: if the platform is down, the status page allows users to check whether it is a known issue being addressed rather than a problem with their own internet connection. The status page is linked from the shelter's main website and from the donation form's error state.

## Acceptance Criteria

- GET /health endpoint returns 200 with status, timestamp, database, and version fields
- GET /health returns 503 with descriptive database field when database is unreachable
- GET /health returns no-store Cache-Control header
- UptimeRobot configured with health check monitor, animal listing monitor, and SSL certificate monitor
- Alert fires after two consecutive failed checks (not on first failure)
- Email alert channel configured with shelter owner's address
- Slack secondary channel configured and tested
- Response time alert fires when health endpoint exceeds two seconds for three consecutive checks
- Public status page configured on a status subdomain
- On-call runbook at docs/operations/oncall-runbook.md covering the four primary failure scenarios
