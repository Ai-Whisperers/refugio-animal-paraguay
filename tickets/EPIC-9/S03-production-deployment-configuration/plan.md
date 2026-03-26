# S03: Production Deployment Configuration

**Epic**: EPIC-9: Docker and Container Setup
**User Story ID**: RAP-S03
**Sprint**: Sprint 2 (estimated)
**Status**: Planning
**Complexity**: Complex (spans infrastructure, secrets, configuration)

---

## User Story

As a DevOps engineer, I want production environment configuration with secrets management, traffic routing, and database connectivity so that the application can be deployed safely to production without exposing credentials or disrupting availability.

---

## Acceptance Criteria

### 1. Secrets Management Implementation

**Criterion**: Implement secure credential storage and injection for production environment.

**Details**:
- Create GitHub Actions repository secrets for production credentials:
  - `PROD_DOCKER_USERNAME` — Docker Hub authentication
  - `PROD_DOCKER_PASSWORD` — Docker Hub authentication
  - `PROD_DATABASE_PASSWORD` — PostgreSQL admin password
  - `PROD_REDIS_PASSWORD` — Redis authentication
  - `PROD_JWT_SECRET_KEY` — JWT signing key (min 32 bytes, cryptographically random)
  - `PROD_STRIPE_SECRET_KEY` — Stripe API secret key
  - `PROD_EMAIL_SERVICE_PASSWORD` — Email service credentials
  - `PROD_DATABASE_URL` — PostgreSQL connection string (format: `postgresql://user:password@host:5432/refugio_prod`)
- Document secret rotation procedures with 90-day cycle
- Implement secret validation in CI/CD pipeline (no hardcoded values in code or workflow YAML)
- Create `.env.production.example` template (committed) showing required variables without values
- Implement AWS Secrets Manager integration for additional security layer (optional for phase 1)

**Verification**:
- All production credentials stored as repository secrets
- No credentials visible in GitHub Actions logs
- Secret rotation documented and tested
- `.env.production.example` committed and up-to-date

---

### 2. Docker Compose Production Override

**Criterion**: Create production-grade `docker-compose.prod.yml` with optimized settings and health checks.

**Details**:
```yaml
# docker-compose.prod.yml
version: '3.9'
services:
  fastapi-backend:
    image: refugio-animal-paraguay/fastapi-backend:${CI_COMMIT_SHA}
    container_name: refugio-api-prod
    restart: always
    environment:
      DATABASE_URL: ${PROD_DATABASE_URL}
      JWT_SECRET_KEY: ${PROD_JWT_SECRET_KEY}
      STRIPE_SECRET_KEY: ${PROD_STRIPE_SECRET_KEY}
      ENVIRONMENT: production
      LOG_LEVEL: info
    ports:
      - "127.0.0.1:8000:8000"  # Bind to localhost only, use reverse proxy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - refugio-network
    volumes:
      - ./logs:/app/logs  # Persistent logs
    depends_on:
      postgres-db:
        condition: service_healthy
      redis-cache:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres-db:
    image: refugio-animal-paraguay/postgres-db:${CI_COMMIT_SHA}
    container_name: refugio-db-prod
    restart: always
    environment:
      POSTGRES_PASSWORD: ${PROD_DATABASE_PASSWORD}
      POSTGRES_DB: refugio_prod
      POSTGRES_USER: refugio_app
    ports:
      - "127.0.0.1:5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U refugio_app -d refugio_prod"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - refugio-network
    volumes:
      - postgres-data-prod:/var/lib/postgresql/data
      - ./backups:/backups  # Backup directory
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  redis-cache:
    image: refugio-animal-paraguay/redis-cache:${CI_COMMIT_SHA}
    container_name: refugio-redis-prod
    restart: always
    environment:
      REDIS_PASSWORD: ${PROD_REDIS_PASSWORD}
    ports:
      - "127.0.0.1:6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - refugio-network
    volumes:
      - redis-data-prod:/data
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '500m'
          memory: 256M

volumes:
  postgres-data-prod:
    driver: local
  redis-data-prod:
    driver: local

networks:
  refugio-network:
    driver: bridge
```

- Configure restart policies: `always` for critical services
- Define resource limits (CPU, memory) for container orchestration
- Expose services only to localhost (127.0.0.1) — Nginx reverse proxy will handle external traffic
- Configure health checks with appropriate intervals and retries
- Add persistent volume mounts for database and cache data
- Set production-appropriate log levels and environment variables

**Verification**:
- `docker-compose.prod.yml` created and validated with `docker-compose config`
- All services have health checks defined
- Resource limits are reasonable for target infrastructure
- No hardcoded credentials in compose file
- Services depend on health checks (not just startup)

---

### 3. Nginx Reverse Proxy Configuration

**Criterion**: Configure Nginx as reverse proxy with SSL/TLS, rate limiting, and request routing.

**Details**:
```nginx
# docker/nginx/prod.conf
upstream fastapi {
    server fastapi-backend:8000;
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=payment_limit:10m rate=1r/s;

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name refugio-animal.org www.refugio-animal.org;

    # SSL certificates (provided via environment or mounted secrets)
    ssl_certificate /etc/ssl/certs/refugio-animal.org.crt;
    ssl_certificate_key /etc/ssl/private/refugio-animal.org.key;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Client body size limit (multipart file uploads)
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/xml text/javascript
               application/x-javascript application/json;
    gzip_min_length 1000;

    location / {
        # Rate limiting
        limit_req zone=general_limit burst=20 nodelay;

        proxy_pass http://fastapi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    location /api/auth/login {
        # Stricter rate limiting for authentication endpoints
        limit_req zone=auth_limit burst=5 nodelay;
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/donations {
        # Strictest rate limiting for payment endpoints
        limit_req zone=payment_limit burst=2 nodelay;
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        access_log off;
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
    }

    location ~ ~$ {
        deny all;
        access_log off;
    }
}
```

- Configure SSL/TLS with modern protocols (TLSv1.2+)
- Implement rate limiting zones (general: 100 req/s, auth: 5 req/s, payment: 1 req/s)
- Add security headers (HSTS, X-Frame-Options, CSP, etc.)
- Configure upstream connection to FastAPI backend
- Enable gzip compression for response optimization
- Set appropriate timeouts and buffer sizes
- Deny access to sensitive files (dot-files, backups)

**Verification**:
- Nginx config validates with `nginx -t`
- SSL certificates properly mounted and valid
- Rate limiting thresholds tested under load
- Security headers present in HTTP responses
- Compression working (test with curl -H "Accept-Encoding: gzip")

---

### 4. Database Backup and Recovery Strategy

**Criterion**: Implement automated PostgreSQL backups with documented recovery procedures.

**Details**:
- Create backup script (`scripts/backup-database.sh`):
  ```bash
  #!/bin/bash
  BACKUP_DIR="./backups"
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_FILE="$BACKUP_DIR/refugio_backup_$TIMESTAMP.sql.gz"

  mkdir -p $BACKUP_DIR

  docker exec refugio-db-prod pg_dump -U refugio_app refugio_prod | \
    gzip > $BACKUP_FILE

  # Keep only last 30 daily backups
  find $BACKUP_DIR -name "refugio_backup_*.sql.gz" -mtime +30 -delete

  echo "Backup completed: $BACKUP_FILE"
  ```
- Configure automated backup schedule via cron (daily at 2 AM UTC):
  ```
  0 2 * * * /path/to/backup-database.sh >> /var/log/refugio-backup.log 2>&1
  ```
- Document recovery procedure:
  1. Identify backup file from `/backups` directory
  2. Stop application: `docker-compose -f docker-compose.prod.yml down fastapi-backend`
  3. Restore database: `docker exec refugio-db-prod psql -U refugio_app refugio_prod < /backups/backup_file.sql`
  4. Restart application: `docker-compose -f docker-compose.prod.yml up -d fastapi-backend`
  5. Verify recovery with health checks
- Implement off-site backup replication (AWS S3 or similar)
- Test recovery procedures monthly

**Verification**:
- Backup script creates valid compressed backups
- Backup schedule configured and verified
- Recovery procedure tested and documented
- Off-site replication configured (if applicable)
- Backup retention policy enforced

---

### 5. Log Aggregation and Rotation

**Criterion**: Configure centralized logging with log rotation and archive strategy.

**Details**:
- Create log rotation configuration (`docker/logrotate.conf`):
  ```
  /var/lib/docker/containers/*/*-json.log
  /app/logs/*.log
  {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
  }
  ```
- Configure Docker logging driver in `docker-compose.prod.yml`:
  ```yaml
  fastapi-backend:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
        labels: "service=fastapi,environment=production"
  ```
- Mount volume for application logs: `./logs:/app/logs`
- Log aggregation destinations:
  - Local: `/app/logs/` (rotated daily)
  - CloudWatch/ELK: Optional cloud provider integration
  - Structured logging format: JSON (timestamp, level, service, message, context)
- Monitor log size and implement cleanup for files older than 90 days

**Verification**:
- Logs rotate correctly and compress
- Log format is consistent across services
- Log volume mount persists across container restarts
- Old log files archived/deleted per policy

---

### 6. Environment-Specific Configuration

**Criterion**: Create environment-specific configuration files with clear separation of concerns.

**Details**:
- Create production environment template (`.env.production.example`):
  ```
  # Database Configuration
  DATABASE_URL=postgresql://refugio_app:YOUR_PASSWORD@postgres-db:5432/refugio_prod
  POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD

  # Redis Configuration
  REDIS_PASSWORD=YOUR_REDIS_PASSWORD

  # Application Settings
  ENVIRONMENT=production
  DEBUG=false
  LOG_LEVEL=info

  # JWT Configuration
  JWT_SECRET_KEY=YOUR_RANDOM_32_BYTE_KEY
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30

  # Stripe Configuration
  STRIPE_SECRET_KEY=sk_live_XXXXXXXXXXXX
  STRIPE_PUBLIC_KEY=pk_live_XXXXXXXXXXXX

  # Email Service Configuration
  EMAIL_SERVICE_PROVIDER=sendgrid
  EMAIL_SERVICE_PASSWORD=YOUR_SENDGRID_KEY
  FROM_EMAIL=notifications@refugio-animal.org

  # CORS and Security
  ALLOWED_ORIGINS=["https://refugio-animal.org", "https://www.refugio-animal.org"]
  CORS_CREDENTIALS=true

  # Feature Flags
  ENABLE_ADOPTION_REQUESTS=true
  ENABLE_DONATIONS=true
  ENABLE_VOLUNTEER_SIGNUP=true
  ```
- Create deployment checklist (`docs/DEPLOYMENT_CHECKLIST.md`):
  - [ ] All required environment variables set
  - [ ] Database migrations applied
  - [ ] SSL certificates installed and valid
  - [ ] Backup procedures tested
  - [ ] Health checks passing
  - [ ] Rate limits configured
  - [ ] Logging aggregation active
  - [ ] Monitoring alerts configured
  - [ ] Rollback procedure ready

**Verification**:
- `.env.production.example` matches actual environment variables
- Deployment checklist is comprehensive and testable
- Configuration can be injected via GitHub Secrets

---

## Definition of Done

- [ ] All acceptance criteria met and verified
- [ ] `docker-compose.prod.yml` created and tested
- [ ] Nginx reverse proxy configuration complete with SSL/TLS
- [ ] Database backup script implemented and scheduled
- [ ] Log rotation configured and working
- [ ] Environment variables documented in `.env.production.example`
- [ ] Secrets management implemented in GitHub Actions
- [ ] Health checks defined for all services
- [ ] Rate limiting thresholds verified under load
- [ ] Recovery procedures documented and tested
- [ ] Zero linting/type errors in all configuration files
- [ ] Security scan clean (no critical/high vulnerabilities)
- [ ] Deployment checklist created and walkthrough completed
- [ ] Documentation updated (README, runbooks)
- [ ] PR submitted with all changes reviewed
- [ ] Staging deployment verified before production

---

## Dependencies

- S01: Docker and Container Setup (completed — provides base images)
- S02: CI/CD Pipeline Integration (completed — provides image building and registry push)
- Infrastructure access (SSL certificates, domain configuration, secret management capability)
- Production database instance or managed database service

---

## Timeline

- **Estimated Duration**: 2-3 days
- **Key Milestones**:
  - Day 1: Secrets management + docker-compose.prod.yml
  - Day 2: Nginx configuration + SSL/TLS
  - Day 3: Backup/recovery + logging setup + documentation

---

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| SSL certificate expiration | Medium | High | Implement certificate renewal automation (Let's Encrypt) |
| Database corruption | Low | Critical | Implement automated backups with tested recovery |
| Configuration drift | Medium | Medium | Version control all configuration files, automate deployment |
| Rate limiting too strict | Medium | High | Load test thoroughly before production |
| Secret exposure in logs | Low | Critical | Review logs for credential patterns, use structured logging |

---

## Reference Examples

### Deployment Workflow (High-Level)

```bash
# 1. Set production environment
export ENVIRONMENT=production
export CI_COMMIT_SHA=$(git rev-parse --short HEAD)

# 2. Pull latest images
docker pull refugio-animal-paraguay/fastapi-backend:${CI_COMMIT_SHA}
docker pull refugio-animal-paraguay/postgres-db:${CI_COMMIT_SHA}
docker pull refugio-animal-paraguay/redis-cache:${CI_COMMIT_SHA}

# 3. Bring up services (assumes .env.production sourced)
docker-compose -f docker-compose.prod.yml up -d

# 4. Run migrations
docker exec refugio-api-prod alembic upgrade head

# 5. Verify health
docker-compose -f docker-compose.prod.yml ps
curl https://refugio-animal.org/health

# 6. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f fastapi-backend
```

### Rollback Workflow (Emergency)

```bash
# 1. Identify previous stable tag
git describe --tags --abbrev=0

# 2. Update image tag in docker-compose.prod.yml
# Change: refugio-animal-paraguay/fastapi-backend:${CI_COMMIT_SHA}
# To: refugio-animal-paraguay/fastapi-backend:v1.0.0  (previous stable)

# 3. Bring down current deployment
docker-compose -f docker-compose.prod.yml down fastapi-backend

# 4. Pull and start previous version
docker pull refugio-animal-paraguay/fastapi-backend:v1.0.0
docker-compose -f docker-compose.prod.yml up -d fastapi-backend

# 5. Verify health
curl https://refugio-animal.org/health

# 6. Create incident ticket to investigate root cause
```

---

## Notes

- Production deployment should follow blue-green or canary strategies for zero-downtime releases (to be covered in S04)
- Monitoring and alerting (health checks, log aggregation, performance metrics) covered in S04
- Disaster recovery beyond backup/restore (multi-region, failover) out of scope for Phase 1
- This story focuses on configuration; actual infrastructure provisioning assumes target environment exists

