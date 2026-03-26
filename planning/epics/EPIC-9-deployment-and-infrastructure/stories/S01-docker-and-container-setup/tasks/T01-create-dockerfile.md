---
task: T01
story: S01
epic: EPIC-9
status: complete
priority: medium
created: 2026-03-25T17:13:26.736184
---

# T01: Create Dockerfile

## Overview

The Dockerfile for Refugio Animal Paraguay follows a multi-stage build pattern that separates the compilation and build environment from the optimized runtime environment. This approach significantly reduces the final image size while maintaining all necessary functionality. The application will run as a non-root user for security, include health checks for orchestration readiness, and implement graceful shutdown handling for clean container termination. The final image targets less than 200 megabytes, achieved through careful base image selection, aggressive dependency management, and strategic layer caching.

## Multi-Stage Build Architecture

The Dockerfile is divided into two distinct stages. The builder stage contains all compilation tools, development headers, and build-time dependencies necessary to install Python packages with compiled C extensions. This stage includes the full Python development environment, system package managers, and build utilities. Once all application dependencies are compiled and optimized, artifacts from this stage are copied into the runtime stage, which uses a minimal Python 3.12-slim base image containing only what is necessary to execute the application.

The builder stage uses python:3.12-full as its base, which includes development headers, gcc, and other compilation tools necessary for packages with C bindings like psycopg2, Redis client libraries, and cryptographic packages. During the build phase, all system packages are installed, Python dependencies are compiled in a dedicated virtual environment, and wheels are cached for fast rebuilds. The runtime stage then copies only the compiled virtual environment from the builder stage, eliminating the need for build tools in the final image.

This separation provides two critical benefits. First, the final runtime image contains none of the build infrastructure, reducing size from over 900 megabytes with a full Python installation to approximately 200 megabytes with only runtime dependencies. Second, Docker's layer caching system can reuse previously built dependency layers when application code changes, since dependencies are built in earlier layers that change less frequently than application code.

## Non-Root User Configuration

The application must run as a non-root user for security compliance and production hardening. This prevents container escape vulnerabilities from granting root access to the host system. The Dockerfile creates a dedicated application user named appuser with minimal privileges, no shell access, and a home directory where runtime temporary files can be safely stored.

User creation happens in both the builder stage and the runtime stage. In the builder stage, the appuser account ensures that any build artifacts created have consistent ownership. In the runtime stage, the account is recreated with identical UID and GID values to maintain consistency across stages, preventing permission issues when mounted volumes are accessed. The UID and GID are explicitly set to fixed values rather than auto-assigned to guarantee reproducibility across rebuilds.

The appuser account has no login shell assigned, only bin/false, preventing direct access even if credentials were somehow compromised. The home directory is created with restricted permissions, allowing the user to write temporary files if needed but preventing directory listing or traversal. The appuser is the default USER specified at the end of the Dockerfile, ensuring all application processes run with these restrictions regardless of how the container is invoked.

## Health Check Implementation

Health checks enable container orchestration systems to determine service readiness and restart failing containers automatically. The Dockerfile includes a HEALTHCHECK instruction that periodically sends HTTP GET requests to the application's /health endpoint. The health check runs every 30 seconds after an initial 10-second startup grace period, with a 5-second timeout for each check. If three consecutive checks fail, the container is marked unhealthy.

The health check command uses curl to perform the HTTP request against http://localhost:8000/health, checking for a 200 status code indicating the application is running and database connections are available. The endpoint should verify not only that the FastAPI application is responding, but also that critical dependencies like PostgreSQL and Redis connectivity are functional. This prevents the container from being marked healthy while waiting for database initialization to complete.

In a Docker Compose environment with multiple services, this health check allows the compose file to properly order service startup using depends_on with the condition service_healthy. The API service will not be declared ready for traffic until its health check passes, preventing connection errors during the database initialization phase when Alembic migrations are running.

## Graceful Shutdown Handling

Graceful shutdown ensures that in-flight requests complete before the container terminates, preventing client errors and data corruption. When a container receives a SIGTERM signal, the application must stop accepting new requests, wait for existing requests to complete, and then exit cleanly. The entrypoint script and FastAPI application configuration work together to implement this behavior.

The entrypoint script runs the FastAPI application using Uvicorn, which is configured to handle SIGTERM signals gracefully. Uvicorn receives the SIGTERM signal, stops accepting new connections, waits for existing requests to complete up to a timeout period, and then exits. The Docker daemon provides a grace period before sending SIGKILL, defaulting to 10 seconds, which is sufficient for most request workloads.

The Dockerfile sets the container's default command to run Uvicorn with the application module, with proper signal handling and timeout configuration. The entrypoint script performs database initialization tasks before starting the application, ensuring migrations run with exclusive database locks before the application attempts connections. This prevents race conditions where multiple container instances try to run migrations simultaneously.

## Layer Caching and Build Optimization

Docker builds images as sequences of layers, where each instruction creates a new layer. If the contents of a layer do not change, Docker reuses the cached layer from a previous build, dramatically accelerating subsequent rebuilds. The Dockerfile is structured with this caching pyramid in mind, placing stable, slow-changing instructions before frequently changing instructions.

Base image selection happens first, as the Python 3.12-slim base image rarely needs updates. System package installation comes next, since the set of required system dependencies changes infrequently during development. Python dependency installation follows, with requirements pinned to specific versions so rebuilds skip this expensive step when the requirements file has not changed. Application code is copied last, since code changes frequently during development and should invalidate the cache to ensure fresh builds.

Within the Python dependency layer, the Dockerfile copies the requirements file into the container before installing dependencies. This allows Docker to cache the dependency installation layer separately from the code layer. When only application code changes, the dependency installation layer is reused from cache, saving minutes of build time that would otherwise be spent recompiling C extensions for packages like psycopg2.

The builder stage uses a similar strategy, installing system build tools and base Python packages in cached layers, then copying the requirements file and creating a virtual environment in a separate layer. The virtual environment is created with specific cache busting behavior where requirements changes invalidate the cache but Python version changes do not, assuming backward compatibility within minor version changes.

## Base Image Selection

Python 3.12-slim is selected as the base image for its balance between functionality and size. The full Python 3.12 image provides development headers and compilation tools, totaling approximately 900 megabytes. The slim variant removes these development dependencies, reducing size to approximately 150 to 160 megabytes while retaining all runtime libraries necessary for compiled packages. Alpine-based images reduce size further to 50 to 80 megabytes but lack C standard libraries needed for cryptographic packages and some database drivers, introducing compatibility risks.

The slim variant is ideal for Refugio Animal Paraguay's architecture because it accommodates psycopg2 for PostgreSQL connectivity, cryptographic libraries for JWT authentication, and HTTP client libraries for Stripe integration, all without requiring build tools in the final image. The baseline slim image size leaves approximately 20 to 50 megabytes for application dependencies, aligning with calculated dependency footprints.

## Dependency Optimization

The Dockerfile implements dependency optimization to stay within the 200-megabyte image size target. FastAPI with Uvicorn adds approximately 5 megabytes, SQLAlchemy with database drivers adds 10 to 15 megabytes, and additional packages like Redis clients, cryptographic libraries, and HTTP utilities add 5 more megabytes. This totals approximately 30 megabytes for production dependencies, well within the available space budget.

The entrypoint script uses a .dockerignore file to exclude unnecessary files from the build context, preventing large test fixtures, documentation, and cache directories from being copied into the image. Cache optimization is further achieved by using pip with the --no-cache-dir flag to avoid storing downloaded wheels in the layer, and by upgrading pip and setuptools to current versions before dependency installation to minimize redundant rebuilds.

Development dependencies are not included in the final image. The builder stage uses a requirements-dev.txt file during development if needed, but the production requirements file contains only runtime dependencies. This separation is crucial for the size target, as development dependencies like pytest, flake8, and documentation tools easily add 20 to 30 megabytes.

## Secret Prevention and Build Security

The Dockerfile must prevent credential leakage into image layers. The .dockerignore file explicitly excludes .env files, credential files, SSH keys, and API key files from being copied into the container. This prevents accidental inclusion of secrets during the COPY instruction.

Build-time secrets should never be included in the Dockerfile as RUN instructions that reference environment variables, as these are persisted in image layers. If the application requires configuration at build time, environment variables should be passed at runtime, not build time. The entrypoint script retrieves runtime configuration from environment variables injected by Docker Compose, keeping secrets out of the image entirely.

Build arguments are used only for non-secret configuration like version numbers or build flags. Any step in the Dockerfile that might expose secrets in error messages is wrapped in shell logic that prevents error output from being retained in the layer. The docker build command should never be invoked with --build-arg flags containing secrets.

For the Refugio Animal Paraguay project, the database connection string, JWT secret key, Stripe API key, and all authentication credentials are provided at runtime via Docker Compose environment variables, never during build. The Dockerfile contains no hardcoded secrets, credential templates, or references to credential files.

## Integration with Docker Compose

The Dockerfile is designed to work seamlessly with docker-compose.yml where the FastAPI service depends on PostgreSQL and Redis services becoming healthy before the API starts accepting traffic. The health check endpoint implementation allows docker-compose to use the condition service_healthy in its depends_on specification.

The application reads database connection parameters from environment variables provided by Docker Compose, connecting to the PostgreSQL service via the service name "database" on the default docker network. Similarly, Redis is accessed via the service name "redis" on the same network. These environment variable defaults are set in the Dockerfile, but are overridden by compose for different deployment environments.

The entrypoint script runs database migrations before starting the application, ensuring the schema is initialized before the application attempts connections. This is safe even when multiple containers start simultaneously because PostgreSQL provides exclusive locking on the migrations table, preventing concurrent migration execution. The health check only reports success after both the application is responding and the database is accessible, ensuring compose does not mark the service as healthy during migration.

## Acceptance Criteria

- [x] Dockerfile created with multi-stage build pattern separating builder and runtime stages
- [x] Non-root application user (appuser) configured with restricted home directory
- [x] Health check endpoint configuration for Docker orchestration
- [x] Graceful shutdown handling through SIGTERM signal management
- [x] Layer caching optimization with stable-first sequencing
- [x] Base image selection rationale documented (Python 3.12-slim chosen)
- [x] Dependency optimization strategies documented and integrated
- [x] Secret prevention mechanisms documented and implemented
- [x] Integration with docker-compose setup and database initialization
- [x] Final image size targeting less than 200 megabytes verified

