# S02 Plan: CI/CD Pipeline Integration

## Story
As a **DevOps engineer**, I want **automated Docker image building and registry push via GitHub Actions** so that **container images are consistently built, tested, and published without manual intervention**.

## Context
Docker containers created in S01 need automated build and deployment pipeline. Every commit to develop/main branch should trigger image builds, run quality checks, and push to Docker registry (Docker Hub or equivalent). This enables Phase 1 data layer work to depend on consistent, automated image delivery.

## Acceptance Criteria

### 1. GitHub Actions Workflow Setup
- [ ] Workflow file created at `.github/workflows/docker-build.yml`
- [ ] Workflow triggers on push to `develop` and `main` branches
- [ ] Workflow triggers on pull requests to validate changes
- [ ] Workflow uses matrix strategy to build multiple images in parallel (fastapi, postgres, redis)
- [ ] Build context correctly specified for each Dockerfile

### 2. Docker Image Building
- [ ] FastAPI backend image builds successfully with multi-stage optimization
- [ ] PostgreSQL image builds successfully with initialization scripts
- [ ] Redis image builds successfully with configuration file
- [ ] All images tagged with: `{image}:latest` for main branch, `{image}:{commit-sha}` for develop, `{image}:pr-{pr-number}` for PRs
- [ ] Build logs captured in workflow summary
- [ ] Build duration < 5 minutes per image (excluding cache rebuild)

### 3. Code Quality in Pipeline
- [ ] FastAPI image includes linting check step (flake8, black, isort)
- [ ] FastAPI image includes type check step (mypy)
- [ ] FastAPI image includes security scan (bandit)
- [ ] Tests run inside container before image push (pytest)
- [ ] Coverage report generated and published
- [ ] Pipeline fails if coverage drops below 80%

### 4. Docker Registry Push
- [ ] Registry credentials secured as GitHub secrets (DOCKER_USERNAME, DOCKER_PASSWORD)
- [ ] Images pushed to Docker Hub with proper naming: `{org}/{image}:{tag}`
- [ ] Push only happens after all quality checks pass
- [ ] Push only happens on successful merge to develop/main (not on PR)
- [ ] Pushed images are publicly accessible (unless org setting is private)
- [ ] Registry has proper image retention policy (keep last 10 tags per image)

### 5. Workflow Notifications and Reporting
- [ ] Workflow status reported in PR checks (fails PR if quality gates fail)
- [ ] Workflow summary includes build duration, image size, test results
- [ ] On failure, workflow logs are accessible for debugging
- [ ] Slack/Email notification on build failure (optional, future enhancement)
- [ ] Build artifacts archived (test reports, coverage reports) for 30 days

### 6. Security and Secrets Management
- [ ] No secrets hardcoded in workflow file
- [ ] Secrets stored in GitHub repository secrets (not in code)
- [ ] Workflow uses least-privilege approach (specific secret access)
- [ ] `.env` files and credentials never committed or pushed
- [ ] Workflow validates `.env.example` exists but not `.env`
- [ ] No Docker config files with credentials committed

## Definition of Done

- [ ] `.github/workflows/docker-build.yml` created and functional
- [ ] All three Docker images (FastAPI, PostgreSQL, Redis) build successfully in CI
- [ ] Code quality gates integrated into workflow (lint, type check, security scan, tests)
- [ ] Images pushed to Docker Hub with correct tagging strategy
- [ ] GitHub secrets configured for registry credentials
- [ ] Workflow tested: PR → successful build → main merge → images pushed
- [ ] Build time optimized (cache layers, parallel builds)
- [ ] No secrets exposed in logs or artifacts
- [ ] Workflow documentation created (how to manually trigger, how to update credentials)
- [ ] All code follows clean code standards
- [ ] Zero linting warnings or type errors in workflow and supporting scripts
- [ ] Tests pass locally and in CI
- [ ] PR reviewed and merged

## Technical Details

### GitHub Actions Workflow Structure

```yaml
name: Docker Build and Push
on:
  push:
    branches:
      - develop
      - main
  pull_request:
    branches:
      - develop
      - main

env:
  REGISTRY: docker.io
  IMAGE_NAMESPACE: refugio-animal-paraguay

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        image:
          - name: fastapi-backend
            dockerfile: docker/Dockerfile.backend
            context: .
          - name: postgres-db
            dockerfile: docker/Dockerfile.postgres
            context: .
          - name: redis-cache
            dockerfile: docker/Dockerfile.redis
            context: .

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        if: github.event_name == 'push' && (github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main')
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Determine image tag
        id: image-tag
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "tag=latest" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
            echo "tag=${{ github.sha }}" >> $GITHUB_OUTPUT
          else
            echo "tag=pr-${{ github.event.pull_request.number }}" >> $GITHUB_OUTPUT
          fi

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.image.context }}
          file: ${{ matrix.image.dockerfile }}
          push: ${{ github.event_name == 'push' && (github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main') }}
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAMESPACE }}/${{ matrix.image.name }}:${{ steps.image-tag.outputs.tag }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAMESPACE }}/${{ matrix.image.name }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  quality-checks:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install black flake8 isort mypy bandit pytest pytest-cov

      - name: Lint with flake8
        run: flake8 src/ tests/ --count --show-source --statistics

      - name: Format check with black
        run: black --check src/ tests/

      - name: Import sort check with isort
        run: isort --check-only src/ tests/

      - name: Type check with mypy
        run: mypy src/

      - name: Security scan with bandit
        run: bandit -r src/ -f json -o bandit-report.json || true

      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=80 \
            --tb=short

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          fail_ci_if_error: true

  security:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

### Tagging Strategy

**Main Branch (Production)**:
- `refugio-animal-paraguay/fastapi-backend:latest` → always latest production build
- `refugio-animal-paraguay/fastapi-backend:20260325.001` → release tag format (date.sequence)

**Develop Branch (Staging)**:
- `refugio-animal-paraguay/fastapi-backend:{commit-sha}` → full commit hash (7 chars truncated)
- `refugio-animal-paraguay/fastapi-backend:staging` → always latest develop build

**Pull Requests**:
- `refugio-animal-paraguay/fastapi-backend:pr-123` → PR-specific tag (not pushed to Docker Hub)

### Docker Registry Configuration

Docker Hub:
- Organization: `refugio-animal-paraguay` (or user account)
- Three public repositories: `fastapi-backend`, `postgres-db`, `redis-cache`
- Automatically pull from GitHub Actions via webhook (optional)
- Configure image retention: Keep last 10 versions per repo

### Credentials Management

```bash
# GitHub Secrets to configure:
DOCKER_USERNAME    → Docker Hub username (or org name)
DOCKER_PASSWORD    → Docker Hub personal access token (NOT password)
GITHUB_TOKEN       → Auto-generated (has access to repo)

# GitHub Actions has access to:
- Repository code (automatic)
- GitHub Secrets (via ${{ secrets.SECRET_NAME }})
- Build logs (stored 90 days)
- Artifacts (stored 30 days by default)
```

### Troubleshooting and Rollback

```bash
# Manual build (if CI fails):
docker build -f docker/Dockerfile.backend -t refugio-animal-paraguay/fastapi-backend:manual-build .

# Manual push:
docker push refugio-animal-paraguay/fastapi-backend:manual-build

# Rollback to previous image:
# Revert commit in Git, merge will automatically trigger new build

# Check image history:
docker history refugio-animal-paraguay/fastapi-backend:latest
docker inspect refugio-animal-paraguay/fastapi-backend:latest
```

## Dependencies

- **Depends on**: S01 (Docker and Container Setup) — must have working Dockerfiles
- **Depends on**: GitHub repository setup with Actions enabled
- **Blocks**: S03 (Production Deployment Configuration) — needs working CI/CD before production setup
- **Blocks**: Phase 1 Data Layer — automation enables smooth Phase 1 transition

## Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Registry credentials exposed in logs | Security breach | Use GitHub Secrets, audit logs regularly |
| Large image sizes slow down builds | Developer friction | Optimize multi-stage builds, cache layers |
| Quality gate failures block PRs frequently | Development slowdown | Tune thresholds (coverage %, complexity), document expectations |
| Build matrix takes too long | Slow feedback loop | Run in parallel, use caching, consider splitting jobs |
| Docker Hub rate limits on pulls | CI pipeline failures | Use paid account or self-hosted registry, implement caching |

## Success Metrics

- All three Docker images build successfully in < 5 minutes total
- PR checks fail when code doesn't meet quality gates (lint, type check, security, tests)
- Images successfully pushed to Docker Hub after merge to develop/main
- Build logs are clear and debuggable (no cryptic error messages)
- Zero secrets exposed in any CI logs or artifacts
- Developer confidence: Can trigger rebuild manually if needed
- Coverage reports visible in GitHub (via Codecov badge)
