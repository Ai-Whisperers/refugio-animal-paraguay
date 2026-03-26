---
task: T02
story: S01
epic: EPIC-9
title: Setup docker-compose
status: ready
priority: medium
created: 2026-03-25T17:13:26.736239
---

# T02: Setup docker-compose

## Description

Setup docker-compose

## Acceptance Criteria

- [ ] Implementation complete
- [ ] Code reviewed
- [ ] Tests written and passing
- [ ] Documentation updated

## Implementation Notes

The docker-compose configuration for Refugio Animal Paraguay establishes a complete local development environment that mirrors production architecture while accommodating the rapid iteration needs of a small development team. This environment comprises three core services: the FastAPI application server, a PostgreSQL database, and a Redis instance for caching and session management.

The primary docker-compose.yml file defines the orchestration of these three services in a way that allows developers to start the entire stack with a single command. The API service runs the FastAPI application through a uvicorn ASGI server, listening on port 8000 and forwarding requests through to the host machine. The database service runs PostgreSQL 16 on port 5432, using a PostgreSQL-specific image that includes necessary extensions for the adoption tracking and donor management workflows. The Redis service operates on port 6379, providing in-memory caching for donation verification tokens and session state to reduce database load during peak user traffic.

Environment variable injection follows a careful pattern to separate configuration from application code. Rather than hardcoding database credentials, service hostnames, or API keys directly into the application, all configuration flows through a .env file that developers maintain locally. This .env file is never committed to version control, existing only on each developer's machine and in secured CI/CD environments. The docker-compose configuration reads from this .env file and injects variables into each service's runtime environment. For the API service, this means the DATABASE_URL points to the Docker network hostname of the db service rather than localhost, since containers communicate through Docker's internal DNS. For the database service, environment variables control the initial superuser password and default database name. The Redis service requires minimal configuration but inherits the same pattern for consistency.

Health checks form a critical part of the docker-compose setup, ensuring that services are truly ready before dependent services attempt to use them. The database service includes a health check that attempts to connect using psql and verify that the database is accepting connections. Rather than simply checking if the port is open, this validation ensures the database initialization has completed and the service is ready for queries. The API service includes a health check that performs an HTTP GET request against the /health endpoint, confirming that the FastAPI application has started and can handle requests. These health checks inform Docker Compose's startup dependency system, preventing the API service from attempting connections until the database and Redis services are genuinely ready. This prevents cascading timeout errors during initial startup.

Volume management in the docker-compose configuration addresses two critical concerns: persistent data storage and development workflow efficiency. The database service uses a named volume for PostgreSQL's data directory, ensuring that data persists even when containers are stopped and removed. This named volume approach is superior to host-mounted directories for database containers because it avoids permission conflicts between the container's postgres user and the host's users. When a developer stops the application with docker-compose down, the data remains intact; the next docker-compose up restores the application with the previous state. For Redis, a named volume similarly preserves session and cache data across container restarts, though Redis data is typically less critical for development purposes. The API service uses a bind mount to connect the host's source code directory to the container's application directory, enabling hot reload of code changes without rebuilding the image. This dramatically accelerates development feedback loops; changing a Python file and refreshing the browser immediately shows the updated behavior.

The database initialization workflow integrates Alembic migrations into the startup process through an entrypoint script. Rather than manually running migrations after starting docker-compose, the database service executes a startup script that applies all pending migrations automatically. This script checks the current state of the database schema and applies only the migrations needed to reach the latest version. This approach ensures that a fresh clone of the repository immediately produces a fully initialized development environment; a single docker-compose up command yields a working application with all tables, indexes, and seed data in place. For the donor and adoption tracking workflows, this means tables for adopters, animals, adoption requests, donations, and payment tracking are created with proper relationships and constraints.

The docker-compose.override.yml file provides a development-specific configuration layer that augments the base docker-compose.yml without modifying it. This file is automatically loaded by Docker Compose and applies overrides for the local development environment. Within this file, developers can specify that the API service should run in debug mode, that logging should be more verbose, or that the FastAPI reload feature should be enabled to auto-restart the application when code changes. The database service can be configured with additional logging to troubleshoot migration or connection issues. Environment variables can be overridden to use development credentials rather than production credentials, ensuring that payment processing tests use Stripe test keys rather than live keys. This separation of base configuration from development overrides means the base docker-compose.yml remains suitable for CI/CD environments while the .override.yml file stays local and never committed.

Port mapping deserves careful consideration in the docker-compose setup. The API service maps port 8000 inside the container to port 8000 on the host, allowing developers to access the application at localhost:8000. The database service maps port 5432 to 5432, enabling local database tools like pgAdmin or DBeaver to connect directly. Redis maps port 6379 similarly. These mappings assume that a developer does not have conflicting services running on the host. If a developer runs another PostgreSQL instance, the docker-compose setup would fail with a port conflict error. The error message guides developers to either stop the conflicting service or modify the port mapping in the compose file.

Resource constraints in the docker-compose configuration prevent runaway resource consumption during development. The database service typically limits memory to 512MB, the API service to 256MB, and Redis to 128MB. These limits are conservative for development but ensure that a runaway application does not consume all available system memory. Database queries that generate very large result sets will fail rather than consuming unbounded memory. This mirrors production constraints, encouraging developers to write efficient queries during development rather than discovering performance issues later.

Networking in docker-compose operates through an implicit bridge network that connects all defined services. The API service can connect to the database by using the hostname db, which Docker's embedded DNS resolves to the database container's internal IP address. This networking is isolated from the host network; services cannot directly access processes running on the host by hostname. However, the port mappings allow the host to reach services through localhost. This isolation is valuable for development because it prevents accidental reliance on host-local services that would not be available in production.

The docker-compose configuration integrates with the CI/CD pipeline through environment detection. The application code detects whether it is running in Docker by checking the presence of a /.dockerenv file, and when detected, applies development-specific behavior such as automatic database migration. This ensures that developers get a fully functioning environment on docker-compose up without manual intervention, while CI/CD pipelines can also leverage the same compose setup for integration testing.

Debugging within the docker-compose environment uses container logs accessed through docker-compose logs or Docker Desktop's log viewer. The API service logs FastAPI request details and application output to stdout, which docker-compose captures. The database service logs connection attempts and query execution (when slow query logging is enabled). Redis logs eviction and connection events. Developers troubleshoot issues by reading these logs and adjusting configuration or code as needed.

The shutdown behavior of docker-compose is configured to allow graceful termination. When docker-compose down is issued, services receive a SIGTERM signal with a timeout period (default 10 seconds) to shut down cleanly. The API service flushes buffered logs and closes database connections. The database completes any in-flight transactions. Redis persists its data. After the timeout, remaining processes are forcefully terminated. This graceful shutdown sequence prevents data corruption and ensures that databases are in a consistent state.

## Related Issues

- EPIC-9
- S01
