# Skill: CI/CD Patterns
**Domain**: GitHub Actions, deployment workflows, quality gates
**Load when**: Creating or modifying CI/CD pipelines, GitHub Actions workflows, deployment configs

---

## GitHub Actions Conventions (This Project)

### Workflow File Location
All workflows in `.github/workflows/`. Name files descriptively: `ci.yml`, `deploy.yml`, `dependabot.yml`.

### Job Structure Pattern
```yaml
name: CI

on:
  push:
    branches: [main, develop, 'feature/**', 'fix/**']
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/

  type-check:
    needs: lint
    # ... same setup pattern

  test:
    needs: [lint, type-check]
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: refugio_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    env:
      DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/refugio_test
```

### Dependency Caching
Always cache pip. Key on `pyproject.toml` hash:
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}
    restore-keys: ${{ runner.os }}-pip-
```

### Coverage Artifacts
```yaml
- run: pytest --cov=src --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-fail-under=80
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: coverage-report
    path: |
      coverage.xml
      htmlcov/
```

### PostgreSQL Service Container
- Image: `postgres:16-alpine`
- Health check: `pg_isready`
- Test credentials only (never production)
- Port 5432 mapped to runner localhost

### Secret Management
- Use `${{ secrets.NAME }}` for sensitive values
- GitHub Environments for staging/production separation
- Never echo secrets in logs
- Document required secrets in `.env.example`

### Deploy Workflow Pattern
```yaml
on:
  push:
    branches: [main]
    tags: ['release-*']

jobs:
  deploy:
    environment: production  # requires approval
    steps:
      - name: Run tests (reconfirm)
      - name: Build Docker image
        run: docker build -t app:${{ github.sha }} .
      - name: Push to registry
      - name: Deploy
      - name: Smoke test
        run: curl -f https://app.example.com/health
      - name: Rollback on failure
        if: failure()
```

### Branch Protection Rules
```
main:    require PR + 1 review + CI pass + no force push
develop: require PR + CI pass
```

---

## Quality Gate Order (Fast-Fail)

1. **Lint** (ruff) — ~5s, catches syntax/style
2. **Format** (black --check) — ~3s, catches formatting
3. **Type check** (pyright) — ~15s, catches type errors
4. **Test** (pytest + coverage) — ~60s, catches logic errors
5. **Security** (bandit) — ~10s, catches vuln patterns

Each gate blocks the next. Total pipeline: ~90s on cache hit.

---

## Dependabot Configuration
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

---

## Anti-Patterns
- Never use `continue-on-error: true` for quality gates
- Never skip tests with `if: false`
- Never hardcode secrets in YAML
- Never use `latest` for action versions — pin to SHA or major version
- Never run `pip install` without caching
