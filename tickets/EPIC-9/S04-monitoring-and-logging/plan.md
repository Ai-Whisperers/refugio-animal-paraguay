# S04 Plan — Monitoring and Logging

## Objective
Implement comprehensive monitoring, logging, and observability infrastructure that tracks application health, performance metrics, and error patterns in production, enabling rapid incident detection and root cause analysis.

## Description
Monitoring and logging provide visibility into application behavior in production. This story establishes structured logging (JSON format), metrics collection (CPU, memory, request latency, error rates), health checks, alerting rules, and dashboards for observing system state. Essential for maintaining reliability and diagnosing issues before users are impacted.

## Acceptance Criteria

### 1. Structured Logging Implementation
- [ ] Application logs written in JSON format with consistent schema:
  ```json
  {
    "timestamp": "2026-03-25T14:30:45.123Z",
    "level": "INFO|WARNING|ERROR|DEBUG",
    "service": "fastapi-backend|postgres-db|nginx|redis-cache",
    "request_id": "uuid-for-tracing",
    "user_id": "[optional]",
    "message": "human-readable message",
    "context": {
      "endpoint": "/adoptions/submit",
      "method": "POST",
      "status_code": 200,
      "duration_ms": 145,
      "error_type": "[if error]",
      "stack_trace": "[if error]"
    }
  }
  ```
- [ ] Python logging configured with FastAPI integration:
  ```python
  # In main.py
  import logging
  import json
  from pythonjsonlogger import jsonlogger

  # Setup JSON logging
  logger = logging.getLogger()
  logHandler = logging.StreamHandler()
  formatter = jsonlogger.JsonFormatter()
  logHandler.setFormatter(formatter)
  logger.addHandler(logHandler)
  logger.setLevel(logging.INFO)

  # Middleware for request/response logging
  from fastapi.middleware import Middleware
  from fastapi.middleware.cors import CORSMiddleware

  @app.middleware("http")
  async def log_requests(request: Request, call_next):
      request_id = str(uuid.uuid4())
      request.state.request_id = request_id

      start_time = time.time()
      response = await call_next(request)
      duration_ms = (time.time() - start_time) * 1000

      logger.info(
          "HTTP Request",
          extra={
              "request_id": request_id,
              "method": request.method,
              "endpoint": request.url.path,
              "status_code": response.status_code,
              "duration_ms": duration_ms,
          }
      )

      return response
  ```
- [ ] Structured logging in database operations (SQLAlchemy event listeners):
  ```python
  from sqlalchemy import event
  from sqlalchemy.engine import Engine

  @event.listens_for(Engine, "before_cursor_execute")
  def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
      logger.debug("SQL Execute", extra={
          "statement": statement,
          "parameters": parameters
      })

  @event.listens_for(Engine, "after_cursor_execute")
  def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
      logger.debug("SQL Complete", extra={
          "duration_ms": context.execution_options.get("duration", 0)
      })
  ```
- [ ] Error logging with full context:
  ```python
  try:
      await payment_service.process_donation(donor_id, amount)
  except StripeError as e:
      logger.error(
          "Payment processing failed",
          exc_info=True,
          extra={
              "user_id": donor_id,
              "amount": amount,
              "error_type": "StripeError",
              "error_code": e.code
          }
      )
      raise
  ```
- [ ] Logs written to `/app/logs/` mounted volume:
  - `app.log` — all application logs (rotated daily)
  - `access.log` — HTTP access log (Nginx)
  - `error.log` — error-level logs only
  - `database.log` — database operations
  - `payment.log` — payment/Stripe operations (critical for audit)

### 2. Health Check Endpoints
- [ ] `/health` endpoint (HTTP 200) — basic liveness check:
  ```python
  @app.get("/health", tags=["monitoring"])
  async def health_check():
      return {
          "status": "ok",
          "timestamp": datetime.utcnow().isoformat(),
          "version": os.getenv("APP_VERSION", "unknown")
      }
  ```
- [ ] `/health/ready` endpoint — readiness check (DB + Redis connectivity):
  ```python
  @app.get("/health/ready", tags=["monitoring"])
  async def readiness_check():
      try:
          # Check database
          async with db.session() as session:
              await session.execute(text("SELECT 1"))

          # Check Redis
          async with redis.pipeline() as pipe:
              await pipe.ping()

          return {
              "status": "ready",
              "database": "connected",
              "cache": "connected",
              "timestamp": datetime.utcnow().isoformat()
          }
      except Exception as e:
          logger.error("Readiness check failed", exc_info=True)
          raise HTTPException(status_code=503, detail="Service not ready")
  ```
- [ ] `/metrics` endpoint — Prometheus-compatible metrics:
  ```python
  from prometheus_client import Counter, Histogram, Gauge, generate_latest

  request_count = Counter(
      'fastapi_requests_total',
      'Total HTTP requests',
      ['method', 'endpoint', 'status']
  )
  request_duration = Histogram(
      'fastapi_request_duration_seconds',
      'HTTP request duration in seconds',
      ['method', 'endpoint']
  )
  database_connections = Gauge(
      'database_connections_active',
      'Active database connections'
  )

  @app.get("/metrics", tags=["monitoring"])
  async def metrics():
      return Response(generate_latest(), media_type="text/plain")
  ```
- [ ] Health checks used in Docker Compose (httpcheck):
  ```yaml
  services:
    fastapi-backend:
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
        interval: 30s
        timeout: 10s
        retries: 3
        start_period: 40s

    postgres-db:
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U refugio_user -d refugio_db"]
        interval: 10s
        timeout: 5s
        retries: 3

    redis-cache:
      healthcheck:
        test: ["CMD", "redis-cli", "ping"]
        interval: 10s
        timeout: 5s
        retries: 3
  ```

### 3. Metrics Collection and Prometheus Integration
- [ ] Prometheus configuration file (`prometheus.yml`):
  ```yaml
  global:
    scrape_interval: 15s
    evaluation_interval: 15s

  scrape_configs:
    - job_name: 'fastapi-backend'
      static_configs:
        - targets: ['localhost:8000']
      metrics_path: '/metrics'
      scrape_interval: 10s

    - job_name: 'postgres-db'
      static_configs:
        - targets: ['localhost:5432']
      # Requires postgres_exporter running

    - job_name: 'redis-cache'
      static_configs:
        - targets: ['localhost:6379']
      # Requires redis_exporter running

    - job_name: 'nginx'
      static_configs:
        - targets: ['localhost:9113']
      # Requires nginx_exporter running

    - job_name: 'docker'
      static_configs:
        - targets: ['localhost:8080']
      # Requires cAdvisor running
  ```
- [ ] Prometheus added to docker-compose.prod.yml:
  ```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: refugio-prometheus
    restart: always
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - refugio-network
    depends_on:
      - fastapi-backend

  volumes:
    prometheus-data:
  ```
- [ ] Key metrics collected:
  - Request rate (requests/sec by endpoint and method)
  - Request latency (p50, p95, p99 in ms)
  - Error rate (5xx and 4xx by endpoint)
  - Database connection pool usage
  - Database query latency (by table/operation)
  - Redis memory usage and command latency
  - Docker container CPU and memory usage
  - HTTP request size (request/response body sizes)
  - Authentication success/failure rate
  - Payment processing success/failure rate

### 4. Log Aggregation (ELK Stack or CloudWatch)
- [ ] Option A: ELK Stack (Elasticsearch + Logstash + Kibana) for self-hosted:
  ```yaml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: refugio-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "127.0.0.1:9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    networks:
      - refugio-network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: refugio-logstash
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    environment:
      - xpack.monitoring.enabled=false
    ports:
      - "127.0.0.1:5000:5000/udp"
    depends_on:
      - elasticsearch
    networks:
      - refugio-network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: refugio-kibana
    environment:
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    ports:
      - "127.0.0.1:5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - refugio-network
  ```
- [ ] Logstash pipeline configuration (logstash.conf):
  ```
  input {
    udp {
      port => 5000
      codec => json
    }
  }

  filter {
    if [type] == "fastapi" {
      mutate {
        add_field => { "[@metadata][index_name]" => "fastapi-logs" }
      }
    }
    if [level] == "ERROR" {
      mutate {
        add_field => { "alert_required" => true }
      }
    }
  }

  output {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "%{[@metadata][index_name]}-%{+YYYY.MM.dd}"
    }
    if [alert_required] {
      email {
        to => "devops@refugio.org.py"
        subject => "ERROR: %{message}"
        body => "%{message}\n%{context}"
      }
    }
  }
  ```
- [ ] Option B: AWS CloudWatch integration (for cloud-hosted deployments):
  ```python
  import watchtower

  # Add CloudWatch handler to logger
  cloudwatch_handler = watchtower.CloudWatchLogHandler(
      log_group='refugio-animal-paraguay',
      stream_name='production'
  )
  cloudwatch_handler.setFormatter(formatter)
  logger.addHandler(cloudwatch_handler)
  ```
- [ ] Log retention policy: Keep 30 days in hot storage, archive to S3 after 30 days
- [ ] Kibana dashboard created with saved searches:
  - All errors in last 24 hours
  - Slow requests (>1000ms)
  - Failed authentication attempts
  - Failed payment transactions
  - Database query performance

### 5. Alerting Rules (Prometheus + Alert Manager)
- [ ] AlertManager configuration (`alertmanager.yml`):
  ```yaml
  global:
    resolve_timeout: 5m

  route:
    group_by: ['alertname', 'cluster', 'service']
    group_wait: 10s
    group_interval: 10s
    repeat_interval: 12h
    receiver: 'default'
    routes:
      - match:
          severity: critical
        receiver: 'pagerduty'
        continue: true
      - match:
          severity: warning
        receiver: 'email'

  receivers:
    - name: 'default'
      # Silent

    - name: 'pagerduty'
      pagerduty_configs:
        - service_key: '${PAGERDUTY_KEY}'

    - name: 'email'
      email_configs:
        - to: 'devops@refugio.org.py'
          from: 'alerts@refugio.org.py'
          smarthost: 'smtp.gmail.com:587'
          auth_username: '${SMTP_USER}'
          auth_password: '${SMTP_PASS}'

  inhibit_rules:
    - source_match:
        severity: 'critical'
      target_match:
        severity: 'warning'
      equal: ['alertname', 'dev', 'instance']
  ```
- [ ] Prometheus alert rules (`alert.rules.yml`):
  ```yaml
  groups:
    - name: refugio_alerts
      interval: 30s
      rules:
        # High error rate
        - alert: HighErrorRate
          expr: rate(fastapi_requests_total{status=~"5.."}[5m]) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "High error rate detected"
            description: "Error rate is {{ $value }} errors/sec"

        # Slow requests
        - alert: SlowRequests
          expr: histogram_quantile(0.95, fastapi_request_duration_seconds) > 1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "P95 latency exceeds 1 second"
            description: "P95 latency is {{ $value }}s"

        # Database connection pool exhaustion
        - alert: DatabaseConnectionPoolFull
          expr: database_connections_active / database_connections_max > 0.9
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "Database connection pool near exhaustion"
            description: "{{ $value | humanizePercentage }} of connections in use"

        # High memory usage
        - alert: HighMemoryUsage
          expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.85
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Container memory usage is high"
            description: "{{ $value | humanizePercentage }} of memory in use"

        # Service down
        - alert: ServiceDown
          expr: up{job="fastapi-backend"} == 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "FastAPI backend is down"
            description: "Service has been down for more than 1 minute"

        # Payment processing failures
        - alert: HighPaymentFailureRate
          expr: rate(stripe_payment_failures_total[5m]) > 0.1
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "High payment failure rate"
            description: "{{ $value | humanizePercentage }} of payment requests failing"

        # Disk space
        - alert: LowDiskSpace
          expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Low disk space"
            description: "{{ $value | humanizePercentage }} disk space remaining"
  ```
- [ ] AlertManager integrated with docker-compose.prod.yml
- [ ] Alert channels configured: Email (all alerts), PagerDuty (critical only), Slack (optional)

### 6. Dashboards and Observability Visualization
- [ ] Grafana configured as primary dashboard platform:
  ```yaml
  grafana:
    image: grafana/grafana:latest
    container_name: refugio-grafana
    restart: always
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASS}
      - GF_SERVER_ROOT_URL=https://monitoring.refugio.org.py
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    networks:
      - refugio-network
    depends_on:
      - prometheus
  ```
- [ ] Grafana data source configured: Prometheus (http://prometheus:9090)
- [ ] Grafana dashboards created (as JSON files in `./grafana/dashboards/`):
  1. **System Overview**: CPU, memory, disk, network I/O across all containers
  2. **Application Performance**: Request rate, latency (p50/p95/p99), error rate by endpoint
  3. **Database Health**: Connection pool, query latency, slow query log, table sizes
  4. **Business Metrics**: Adoption submissions, donation amount and count, volunteer registrations
  5. **Payment Processing**: Successful transactions, failed transactions, Stripe error breakdown, EUR vs PYG distribution
  6. **User Activity**: Authentication attempts, session count, user roles distribution
  7. **Infrastructure**: Docker container health, resource usage, deployment status
- [ ] Alert notification in Grafana: Email, Slack, PagerDuty integration
- [ ] Kibana dashboard (for ELK stack option) with:
  - Error log explorer (searchable, filterable)
  - Request timeline (requests over time)
  - Endpoint performance comparison (latency by endpoint)
  - Error categorization (by type, endpoint, user)

## Definition of Done
- [ ] Structured logging implemented with JSON format across all services
- [ ] Python logging configured in FastAPI application with middleware
- [ ] Health check endpoints working (/health, /health/ready, /metrics)
- [ ] Docker Compose includes health checks for all services
- [ ] Prometheus configuration complete and scraping metrics
- [ ] AlertManager rules defined with appropriate thresholds
- [ ] Alert channels configured (email at minimum)
- [ ] Grafana dashboards created and displaying metrics
- [ ] Log aggregation working (ELK or CloudWatch)
- [ ] Kibana dashboards/CloudWatch Logs Insights configured
- [ ] Alerting tested: trigger a failure and verify alert is sent
- [ ] Log rotation working (daily, 30-day retention)
- [ ] Documentation updated with monitoring procedures
- [ ] Runbook created for common alerts and remediation
- [ ] Zero linting/type errors
- [ ] Security scan clean (no exposed credentials in logs)
- [ ] All monitoring endpoints protected (auth required or localhost only)
- [ ] PR submitted with monitoring changes
- [ ] Staging environment monitoring verified
- [ ] Production monitoring checklist completed

## Complexity Assessment

**Track**: Complex Implementation

### Justification
- Multiple systems integration (Prometheus, Grafana, ELK/CloudWatch, AlertManager)
- Affects 5+ files (FastAPI app, docker-compose configs, alert rules, dashboard JSON files, documentation)
- Implementation changes exceed 10 lines of code (logging middleware, health endpoints, metrics collection)
- Complex dependencies between monitoring components
- Requires configuration expertise in Prometheus, Grafana, and alerting systems

## Approach

### Phase 1: Structured Logging (1 day)
1. Install `python-json-logger` dependency
2. Configure application logging in FastAPI
3. Add request/response logging middleware
4. Add database operation logging (SQLAlchemy events)
5. Add error logging with context
6. Test logging output format
7. Commit: "S04: Phase 1 — Structured logging implementation"

### Phase 2: Health Checks and Metrics (1 day)
1. Implement `/health` endpoint
2. Implement `/health/ready` endpoint with dependency checks
3. Add Prometheus client library
4. Implement `/metrics` endpoint with key metrics
5. Add health checks to docker-compose.prod.yml
6. Test health endpoints and metrics output
7. Commit: "S04: Phase 2 — Health checks and metrics endpoints"

### Phase 3: Prometheus and Alerting (1 day)
1. Create prometheus.yml configuration
2. Add Prometheus service to docker-compose.prod.yml
3. Create alert.rules.yml with critical alerts
4. Create alertmanager.yml configuration
5. Add AlertManager service to docker-compose.prod.yml
6. Configure alert channels (email, optional PagerDuty)
7. Test alert triggering
8. Commit: "S04: Phase 3 — Prometheus and AlertManager setup"

### Phase 4: Log Aggregation (1 day)
1. Choose ELK or CloudWatch based on deployment location
2. If ELK: Add Elasticsearch, Logstash, Kibana to docker-compose
3. If CloudWatch: Add boto3 and watchtower to requirements
4. Create Logstash pipeline (ELK) or CloudWatch configuration
5. Configure log shipping from application
6. Create Kibana dashboards (ELK) or CloudWatch Logs Insights queries
7. Test log aggregation end-to-end
8. Commit: "S04: Phase 4 — Log aggregation setup"

### Phase 5: Grafana Dashboards (1 day)
1. Add Grafana service to docker-compose.prod.yml
2. Configure Prometheus as data source
3. Create System Overview dashboard
4. Create Application Performance dashboard
5. Create Database Health dashboard
6. Create Business Metrics dashboard
7. Create Payment Processing dashboard
8. Export dashboards as JSON to version control
9. Configure Grafana alerting (send to AlertManager)
10. Commit: "S04: Phase 5 — Grafana dashboards"

### Phase 6: Documentation and Runbooks (1 day)
1. Create MONITORING.md guide
2. Document alert meanings and thresholds
3. Create runbook for common alerts (high error rate, database issues, payment failures)
4. Document dashboard navigation
5. Document log searching in Kibana/CloudWatch
6. Create incident response procedures
7. Document metric definitions
8. Commit: "S04: Phase 6 — Documentation and runbooks"

## Dependencies
- Depends on: S01 (Docker and Container Setup) and S03 (Production Deployment Configuration) completed
- Requires: Prometheus, Grafana, Elasticsearch/CloudWatch access (depending on option chosen)
- Blocked by: None identified

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Logging overhead impacts performance | Medium | Medium | Implement structured logging with async handlers; benchmark before/after |
| Alert fatigue (too many false positives) | Medium | Medium | Carefully tune thresholds during staging; use aggregation/inhibition rules |
| Metrics cardinality explosion | Low | High | Limit label combinations; use recording rules to pre-aggregate high-cardinality metrics |
| ELK stack resource consumption (if chosen) | Medium | Medium | Use Single-Node ES for initial deployment; evaluate CloudWatch cost vs infrastructure cost |
| Unauthorized access to monitoring dashboards | Medium | Medium | Enable Grafana authentication; protect Prometheus endpoint with reverse proxy auth |
| Disk space exhaustion from logs | Medium | High | Implement aggressive log rotation (7-day hot, archive to S3); monitor disk usage |
| Missing critical alerts during setup | Low | High | Test all alert rules with synthetic failure scenarios; maintain runbook |
| Monitoring infrastructure becomes single point of failure | Low | High | Deploy monitoring stack outside main application network if possible; regular backups |
| Secrets exposed in logs | High | Critical | Redact sensitive data (API keys, passwords, PII) at logging point; use structured logging labels carefully |
| Performance metric anomalies not detected | Medium | Medium | Baseline normal values during staging; use anomaly detection rules (optional) |

## Reference Examples

### Monitoring Setup Workflow
```
1. Configure application logging
2. Deploy health check endpoints
3. Start Prometheus and verify metrics collection
4. Configure alerts and AlertManager
5. Deploy log aggregation stack
6. Create Grafana dashboards
7. Test alert flow end-to-end
8. Train team on monitoring tools
9. Monitor production metrics in staging
10. Go live with production monitoring
```

### Emergency Alert Response
```
1. Alert received (PagerDuty/Email)
2. Open Grafana dashboard for service
3. Correlate metrics (error rate, latency, resource usage)
4. Search logs in Kibana/CloudWatch for context
5. Check runbook for alert type
6. Execute remediation steps
7. Verify alert clears
8. Investigate root cause in logs/metrics
9. Plan fix (if code issue)
10. Post-incident review
```

## Timeline

| Milestone | Est. Duration | Owner |
|-----------|---------------|-------|
| Structured Logging | 1 day | Backend Engineer |
| Health Checks & Metrics | 1 day | Backend Engineer |
| Prometheus & Alerting | 1 day | DevOps Engineer |
| Log Aggregation | 1 day | DevOps Engineer |
| Grafana Dashboards | 1 day | DevOps/SRE |
| Documentation & Runbooks | 1 day | All + TechWriter |
| **Total** | **6 days** | — |

**Note**: Phases can overlap (e.g., Prometheus setup during logging phase) to reduce total timeline to 4-5 days.

## Story Points
**8 points** (Complex multi-system integration, cross-team coordination, operational impact)

## Related Stories
- S01: Docker and Container Setup
- S02: CI/CD Pipeline Integration
- S03: Production Deployment Configuration
- Future: Distributed Tracing (OpenTelemetry)
- Future: Custom Metrics for Business KPIs
