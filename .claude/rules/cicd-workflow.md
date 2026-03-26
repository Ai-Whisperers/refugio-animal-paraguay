# Rule: CI/CD Workflow
**ID**: rule.cicd.workflow.v1
**Version**: 1.0.0
**Applies to**: CI/CD pipeline setup and maintenance

---

## 5-Stage Quality Gate Architecture

Every pipeline must implement these stages in order:

```
Stage 1: Build & Validate
  ↓ (fails = block)
Stage 2: Security Scan
  ↓ (Critical/High = block)
Stage 3: Test & Coverage
  ↓ (below threshold = block)
Stage 4: Package & Sign
  ↓ (package errors = block)
Stage 5: Deploy / Publish
```

### Stage 1: Build & Validate

```yaml
# Purpose: Fail fast on code quality issues
steps:
  - install dependencies
  - lint (zero warnings)
  - type check (zero errors)
  - compile/build
  - run unit tests
  - verify documentation completeness
```

**Fail conditions**:
- Any lint warning
- Any type error
- Build failure
- Any test failure

### Stage 2: Security Scan

```yaml
# Purpose: Block vulnerable dependencies and secret exposure
steps:
  - dependency vulnerability scan (pip-audit / npm audit)
  - secret detection (gitleaks / detect-secrets)
  - SAST scan if applicable
```

**Fail conditions**:
- Critical or High severity vulnerability
- Any detected secret or credential
- Known malicious package

### Stage 3: Test & Coverage

```yaml
# Purpose: Enforce quality thresholds by branch
steps:
  - run full test suite
  - generate coverage report
  - enforce threshold:
      main: 80%
      develop: 75%
      feature/*: 70%
  - generate coverage artifact
```

**Fail conditions**:
- Coverage below branch threshold
- Any test failure
- Flaky tests (>1 retry needed) — investigate, don't retry silently

### Stage 4: Package & Sign

```yaml
# Purpose: Create versioned, traceable artifacts
steps:
  - determine version from tag or branch
  - build package/container
  - generate SBOM (Software Bill of Materials)
  - sign artifact
  - attach build metadata (git SHA, timestamp, pipeline ID)
```

### Stage 5: Deploy / Publish

```yaml
# Purpose: Automated deployment with gates
steps:
  - deploy to target environment
  - run smoke tests
  - verify deployment health
  - update deployment record
```

---

## Tag-Based Versioning

### Tag Format

```
[type]-[version][-suffix]
```

### Tag Types

| Tag | Purpose | Pipeline Behavior |
|-----|---------|-----------------|
| `release-1.2.0` | Production release | Full pipeline → deploy to prod |
| `release-1.2.0-rc.1` | Release candidate | Full pipeline → deploy to staging |
| `test-*` | Test pipeline configuration | Runs pipeline, skips deploy |
| `coverage-*` | Coverage analysis only | Runs stages 1-3 only |
| `security-*` | Security audit only | Runs stages 1-2 only |

### Versioning Strategy

Follow Semantic Versioning (`MAJOR.MINOR.PATCH`):

```
MAJOR: Breaking change (API change, database migration requiring downtime)
MINOR: New feature (backwards compatible)
PATCH: Bug fix (backwards compatible)
```

**Pre-release suffixes**:
- `-alpha.N` — Unstable, internal testing
- `-beta.N` — Feature complete, wider testing
- `-rc.N` — Release candidate, final validation

---

## Branch-Specific Pipeline Behavior

| Branch | Trigger | Stages Run | Deploy Target |
|--------|---------|-----------|--------------|
| `feature/*` | PR open/push | 1-3 | None |
| `develop` | Merge | 1-4 | Staging (if tests pass) |
| `release/*` | Merge | 1-4 | Staging |
| `main` | Merge + tag | 1-5 | Production |
| Any `release-*` tag | Tag push | 1-5 | Production |

---

## Local Validation Before Push

```bash
#!/usr/bin/env bash
# scripts/validate-local.sh
set -e

echo "=== Stage 1: Build & Validate ==="
npm run lint           # or: ruff check .
npm run type-check     # or: mypy src/
npm run build          # or: python -m py_compile ...

echo "=== Stage 2: Security ==="
npm audit              # or: pip-audit
# gitleaks detect --source=.

echo "=== Stage 3: Tests ==="
npm test -- --coverage

echo "✅ All local checks passed — safe to push"
```

---

## Environment Configuration

### Environment Variables (never hardcoded)

```yaml
# .env.example (committed — no real values)
DATABASE_URL=postgresql://user:password@localhost:5432/refugio_dev
PAYMENT_API_KEY=your_payment_api_key_here
EMAIL_SERVICE_KEY=your_email_key_here

# .env (never committed — real values)
# Listed in .gitignore
```

### Environment Tiers

| Environment | Purpose | Data | Deploy Trigger |
|-------------|---------|------|---------------|
| `development` | Local dev | Fake/seeded | Manual |
| `staging` | Integration testing | Anonymized copy | develop merge |
| `production` | Live users | Real | release tag |

**Rule**: Never use production credentials in staging or development.

---

## Pipeline Configuration Standards

### YAML Pipeline Quality

```yaml
# ✅ GOOD — Explicit, descriptive step names
- name: "Run unit tests with coverage"
  run: pytest --cov=src --cov-fail-under=80

# ❌ BAD — Opaque
- run: pytest
```

```yaml
# ✅ GOOD — Fail on warning, not just error
- name: "Lint with zero-warning policy"
  run: |
    ruff check . --exit-non-zero-on-fix
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
      echo "🔴 Linting failed — fix all warnings before merging"
      exit 1
    fi
```

### Required Pipeline Outputs

Every pipeline run must produce:
- Build log (always)
- Test results (JUnit XML or equivalent)
- Coverage report (HTML + summary)
- Security scan report
- SBOM (for release builds)

---

## Deployment Rollback

Every deployment must have a defined rollback path:

```bash
# Rollback procedure (document in runbook):
1. Identify previous stable version tag
2. Re-deploy previous version:
   git tag rollback-[date] [previous-stable-sha]
   git push origin rollback-[date]
3. Verify health checks pass
4. Create incident ticket to investigate root cause
```

---

## FINAL MUST-PASS CHECKLIST

Pipeline setup:
- [ ] All 5 stages implemented
- [ ] Zero-warning policy enforced in Stage 1
- [ ] Security scan blocks on Critical/High (Stage 2)
- [ ] Coverage threshold enforced per branch (Stage 3)
- [ ] No secrets in pipeline YAML or logs
- [ ] Tag-based versioning configured
- [ ] Local validation script matches CI stages

Before tagging a release:
- [ ] All tests pass on release branch
- [ ] Security scan clean
- [ ] Coverage above production threshold (80%)
- [ ] CHANGELOG updated
- [ ] Version bumped in appropriate files
- [ ] Release notes prepared
