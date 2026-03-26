---
task: T01
story: S03
epic: EPIC-9
title: Configure hosting
status: ready
priority: medium
created: 2026-03-25T17:13:26.736807
---

# T01: Configure hosting

## Description

Select and configure a production hosting environment for the Refugio Animal Paraguay platform. The hosting decision must balance three constraints: GDPR compliance (EU donor data must remain in the European Economic Area), low latency for the Dutch donor base, and operational simplicity for a small team maintaining a shelter management application. This task covers provider evaluation, server provisioning, environment configuration, and initial deployment verification.

## Hosting Requirements and Constraints

The application has two distinct user populations with different performance expectations. European donors — primarily from the Netherlands and surrounding countries — need fast API responses for the donation flow, which is latency-sensitive because users who perceive a slow checkout are more likely to abandon. The shelter staff in Paraguay need reliable access to animal records and adoption workflows but can tolerate somewhat higher latency because they are internal users on a consistent connection.

GDPR imposes a hard constraint: personal data about EU residents — which includes donor names, email addresses, and payment metadata — must be stored on servers physically located within the European Economic Area. This constraint eliminates hosting providers that only operate in the Americas or Asia-Pacific regions and rules out configurations where the primary database is hosted outside the EEA.

The shelter is a small organization. The hosting solution must be operable by a non-specialist: the owner should be able to understand the monthly invoice, respond to a downtime alert, and restore from backup without engaging a specialist engineer every time.

## Provider Selection

Hetzner Cloud with a datacenter in Germany (Falkenstein or Nuremberg) is the preferred provider. Hetzner is a German company subject to GDPR, its datacenters are in the EEA, its pricing is significantly lower than AWS or Azure for equivalent compute, and its control panel is straightforward enough that a non-engineer can navigate it. The latency from Germany to the Netherlands is under ten milliseconds, which is adequate for the donation flow.

The alternative evaluated but not selected is Fly.io with a region in Amsterdam. Fly.io offers easy container-based deployments and built-in health checks, but its pricing for persistent PostgreSQL storage is less predictable and its support options are limited for a production GDPR workload.

DigitalOcean and Linode were also considered. Both offer European datacenters and clear pricing but provide less advantageous per-gigabyte storage costs for a database that will grow with adoption records and donation history.

## Instance Configuration

The production environment consists of two servers on Hetzner Cloud. The application server runs the FastAPI application in a Docker container. The database server runs PostgreSQL 16, also containerized, with a persistent volume mapped to Hetzner's network-attached block storage for durability.

The separation of application and database onto distinct servers allows each to be scaled independently. If PostgreSQL query performance degrades as record volume grows, the database server can be upgraded to a larger instance without touching the application server. If API throughput becomes the bottleneck, the application server can be replaced with a larger one or a load balancer can be added in front of multiple application instances.

The initial instance sizing is a CX21 (two vCPUs, four gigabytes RAM) for the application server and a CX21 for the database server. This sizing is deliberately modest: at the expected initial traffic volume — hundreds of adoption records, dozens of donors — this is more than sufficient. The instance type can be upgraded through the Hetzner control panel with a brief restart when capacity is needed.

A Hetzner private network connects the application server and the database server so that database traffic does not traverse the public internet. The PostgreSQL port is not exposed to the public internet. The application server accepts traffic only on ports 80 and 443. SSH access is restricted to key-based authentication and is accessible from specific IP addresses specified in a Hetzner firewall rule.

## PostgreSQL Managed vs Self-Hosted

Self-hosted PostgreSQL on the Hetzner database server is the selected approach rather than a managed PostgreSQL service. The rationale is cost: managed PostgreSQL services from Hetzner, DigitalOcean, or AWS RDS cost three to five times more per month than running PostgreSQL on a general-purpose virtual machine. For the expected data volume, the operational overhead of self-hosted PostgreSQL is limited to ensuring daily backups run and the operating system receives security updates.

The backup strategy is: a daily pg_dump scheduled via cron, compressed and encrypted, uploaded to Hetzner Object Storage with a thirty-day retention policy. The restore procedure is documented in docs/operations/database-restore-runbook.md. The oncall person should be able to perform a full restore from the most recent backup within one hour.

If the volume of donation and adoption records grows to the point where backup duration or query performance becomes a concern, migration to a managed PostgreSQL service is the natural upgrade path and does not require application code changes — only the DATABASE_URL environment variable changes.

## Environment Variables and Secrets Management

All application configuration is passed to the FastAPI container via environment variables. Sensitive values — database credentials, the Stripe secret key, the JWT signing secret, the Sentry DSN — are stored in Hetzner's environment configuration (or an equivalent secrets manager) and injected at container startup. They are never written to the Docker image, never committed to the repository, and never logged.

A file named .env.example at the repository root documents the full list of required environment variables with placeholder values, so that a developer setting up a new environment knows exactly which variables to provide without ever seeing the real production values. The production values are stored separately in a password manager (Bitwarden or equivalent) accessible to the owner and any delegated operators.

The ENVIRONMENT environment variable is set to production on the production server, staging on the staging server, and development on local developer machines. The FastAPI application uses this variable to apply environment-specific configuration: Sentry is enabled only in production and staging, the traces sample rate differs per environment, and CORS allowed origins differ per environment.

## Network Topology

Public internet traffic arrives at the application server on port 443 (HTTPS). Traefik handles TLS termination and forwards decrypted requests to the FastAPI application running on port 8000 inside the Docker network. Database connections from the FastAPI application reach the database server via the Hetzner private network on the default PostgreSQL port. The database server has no public IP address — it is only reachable via the private network.

A floating IP address is provisioned and pointed at the application server's public IP. In the event of an application server failure requiring replacement with a new server, the floating IP can be remapped to the replacement server without changing the DNS record, which has a longer TTL.

## Staging Environment

A staging environment on Hetzner uses a smaller CX11 instance for both the application and the database. Staging is used for pre-deployment validation and for running the Locust performance tests described in EPIC-8. Staging uses a separate Stripe test-mode API key and a separate database seeded with anonymized records. The staging domain resolves to the staging server's floating IP. The GitHub Actions deployment pipeline deploys to staging on every merge to the develop branch, and to production only on explicit release tag pushes.

## Acceptance Criteria

A successful outcome for this task means: the production application server and database server are provisioned and connected via a private network; the FastAPI application is accessible at the production domain over HTTPS; environment variables are in place for all required configuration; the staging environment mirrors the production setup with smaller instances; and a brief architecture document at docs/infra/hosting-architecture.md describes the topology, the firewall rules, and the instance sizes so that a future operator can understand the setup without having to discover it.
