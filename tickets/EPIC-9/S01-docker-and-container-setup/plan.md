# S01: Docker and Container Setup — Plan

**Ticket ID**: RAP-S01-001
**Epic**: EPIC-9 (Docker and Container Setup)
**Type**: Story
**Priority**: P0 (Blocks Phase 1)
**Estimate**: 13 points (2-3 sprints)

---

## User Story

As a **developer**, I want **standardized Docker containers for all services (FastAPI, PostgreSQL, Redis)** so that **I can run the complete development environment with consistent configurations across machines**.

---

## Acceptance Criteria

### 1. FastAPI Backend Container

**Given** I have Docker installed on my machine
**When** I run `docker build -f Dockerfile.backend -t refugio-backend:latest .`
**Then** the image builds successfully without errors

**And** when I run the container with `docker run -p 8000:8000 refugio-backend:latest`
**Then** the FastAPI application starts on port 8000 and responds to health checks

**And** when I inspect the image with `docker inspect refugio-backend:latest`
**Then** the image includes:
- Python 3.12 base image
- All dependencies from requirements.txt installed
- Non-root user (appuser) for security
- Health check endpoint configured
- Multi-stage build (builder → runtime)

### 2. PostgreSQL Database Container

**Given** PostgreSQL container is available
**When** I run `docker build -f Dockerfile.postgres -t refugio-postgres:16 .`
**Then** the image builds with PostgreSQL 16 official base image

**And** when I run the container with appropriate environment variables
**Then** the database:
- Initializes with UTF-8 encoding (for Spanish characters)
- Creates specified database and role
- Loads initial schema from mounted SQL files
- Exposes port 5432 for connections
- Includes persistent volume mount point `/var/lib/postgresql/data`

**And** when I connect from FastAPI container
**Then** connection succeeds using PostgreSQL 16 protocol

### 3. Redis Cache Container

**Given** Redis container configuration exists
**When** I run `docker build -f Dockerfile.redis -t refugio-redis:latest .` or use official Redis image
**Then** the container:
- Uses Redis 7.x official image
- Exposes port 6379 for connections
- Includes persistent volume mount point `/data`
- Implements configuration for max memory policy

**And** when I connect from FastAPI container
**Then** connection succeeds and supports SET/GET operations

### 4. Docker Compose Development Stack

**Given** I have all Dockerfiles in the project root
**When** I run `docker-compose up` from project root
**Then** all three services start in correct order:
1. PostgreSQL (initializes first, waits for readiness)
2. Redis (no startup dependencies)
3. FastAPI (waits for PostgreSQL health check)

**And** service connectivity works:
- FastAPI can reach PostgreSQL at `postgres:5432`
- FastAPI can reach Redis at `redis:6379`
- All services have health checks configured

**And** development workflow is enabled:
- Code changes in `src/` directory trigger hot reload in FastAPI
- Database schema changes persist across container restarts
- Redis cache is cleared on container restart (development behavior)

### 5. Container Image Registry

**Given** container images are built locally
**When** I run `docker push refugio-backend:latest` to configured registry
**Then** the image is pushed successfully to Docker Hub or equivalent registry

**And** when a CI/CD pipeline runs
**Then** it can pull images from the registry for deployment

### 6. Documentation and Quick Start

**Given** documentation exists
**When** a new developer reads the Docker setup guide
**Then** they can:
- Understand purpose of each container
- Run complete stack with single command
- Debug common container issues
- Know where to find Dockerfile modifications

**And** when they follow the quickstart
**Then** they achieve:
- Fully functional development environment in <5 minutes
- All services healthy and responsive
- Ability to run tests and make code changes

---

## Definition of Done

- [ ] All Dockerfile configurations created (backend, postgres, redis)
- [ ] docker-compose.yml created with proper service definitions
- [ ] All services pass health checks on startup
- [ ] Documentation created: Docker setup guide, troubleshooting
- [ ] .dockerignore configured to exclude unnecessary files
- [ ] Multi-stage builds optimized for production
- [ ] Environment variables properly managed (.env.example created)
- [ ] Security: Non-root users, no hardcoded credentials
- [ ] All code changes follow clean code standards
- [ ] No linting warnings or type errors
- [ ] Tests pass (unit tests for configuration validation)
- [ ] Pull requests reviewed and approved
- [ ] Branch merged to develop

---

## Technical Details

### Dockerfile Strategy

**Backend Dockerfile** (Multi-stage):
```
Stage 1: builder
  - Python 3.12 slim base
  - Install build dependencies
  - Install Python packages from requirements.txt

Stage 2: runtime
  - Python 3.12 slim base
  - Copy packages from builder
  - Create non-root appuser
  - Set working directory
  - Expose port 8000
  - Add health check
  - Run uvicorn
```

**PostgreSQL Dockerfile**:
```
- Official postgres:16 base image
- Custom initialization scripts in /docker-entrypoint-initdb.d/
- UTF-8 locale configuration
- Persistent volume mount
```

**Redis Dockerfile**:
```
- Official redis:7 base image
- Custom configuration file
- Persistent volume mount
- No modification needed for development
```

### docker-compose.yml Structure

```yaml
version: '3.8'

services:
  postgres:
    build: ./docker/postgres
    environment:
      POSTGRES_DB: refugio_dev
      POSTGRES_USER: refugio
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U refugio"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    build: ./docker/redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./docker/backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://refugio:dev_password@postgres:5432/refugio_dev
      REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./src:/app/src
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

### Security Considerations

1. **Non-root users**: All containers run as non-root appuser
2. **Environment variables**: Passwords in .env.example (sample), real values in .env (git-ignored)
3. **.dockerignore**: Exclude __pycache__, .venv, .git, etc.
4. **Image scanning**: Setup for future vulnerability scanning in CI/CD
5. **Secret management**: Never hardcode credentials in Dockerfile

---

## Dependencies

- **Requires**: Phase 0 completion (tech stack finalized)
- **Blocks**: S02 (CI/CD Pipeline Integration), Phase 1 Data Layer development
- **Related**: Docker installation guide, docker-compose documentation

---

## Success Metrics

1. ✅ New developer can run `docker-compose up` and have complete environment in <5 minutes
2. ✅ All services pass health checks within 30 seconds of startup
3. ✅ Zero build warnings and zero security vulnerabilities in base images
4. ✅ Documentation complete and tested by at least 1 team member
5. ✅ Code review approved (minimum 1 approver)

---

## Notes

- Consider using compose profiles for optional services (monitoring, debugging tools) in future
- Prepare .env.example with all required environment variables
- Document port mappings clearly (8000 for API, 5432 for DB, 6379 for Redis)
- Ensure all Dockerfiles follow Docker best practices (layer caching, minimal base images)
