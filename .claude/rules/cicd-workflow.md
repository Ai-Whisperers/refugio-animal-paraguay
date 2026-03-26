# Rule: CI/CD Workflow
**ID**: rule.cicd.workflow.v1
**Version**: 1.0.0
**Applies to**: CI/CD pipeline setup and maintenance

---

## 5-Stage Quality Gate Architecture

```
Stage 1: Build & Validate    → lint (zero warnings), type check, unit tests
Stage 2: Security Scan       → dependency scan, secret detection, SAST
Stage 3: Test & Coverage     → full test suite, coverage threshold enforcement
Stage 4: Package & Sign      → versioned artifact, SBOM, build metadata
Stage 5: Deploy / Publish    → deploy, smoke tests, health check
```

Each stage blocks the next on failure.

### Fail Conditions by Stage

| Stage | Blocks on |
|-------|-----------|
| 1: Build & Validate | Any lint warning, type error, test failure, build failure |
| 2: Security Scan | Critical/High vulnerability, any detected secret |
| 3: Test & Coverage | Below branch threshold, any test failure, flaky tests |
| 4: Package & Sign | Package errors, signing failure |
| 5: Deploy | Failed smoke tests, health check failure |

---

## Tag-Based Versioning

### Tag Types

| Tag | Purpose | Pipeline Behavior |
|-----|---------|-----------------|
| `release-1.2.0` | Production release | Full pipeline → deploy to prod |
| `release-1.2.0-rc.1` | Release candidate | Full pipeline → deploy to staging |
| `test-*` | Test pipeline configuration | Runs pipeline, skips deploy |
| `coverage-*` | Coverage analysis only | Runs stages 1-3 only |
| `security-*` | Security audit only | Runs stages 1-2 only |

### Semantic Versioning

```
MAJOR: Breaking change (API change, migration requiring downtime)
MINOR: New feature (backwards compatible)
PATCH: Bug fix (backwards compatible)
```

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

## Environment Configuration

### Environment Tiers

| Environment | Purpose | Data | Deploy Trigger |
|-------------|---------|------|---------------|
| `development` | Local dev | Fake/seeded | Manual |
| `staging` | Integration testing | Anonymized copy | develop merge |
| `production` | Live users | Real | release tag |

**Rule**: Never use production credentials in staging or development. All secrets in env vars — never in YAML or code.

---

## Required Pipeline Outputs

Every pipeline run must produce:
- Build log
- Test results (JUnit XML or equivalent)
- Coverage report (HTML + summary)
- Security scan report
- SBOM (for release builds)

---

## FINAL MUST-PASS CHECKLIST

Pipeline setup:
- [ ] All 5 stages implemented
- [ ] Zero-warning policy enforced in Stage 1
- [ ] Security scan blocks on Critical/High (Stage 2)
- [ ] Coverage threshold enforced per branch (Stage 3)
- [ ] No secrets in pipeline YAML or logs
- [ ] Tag-based versioning configured

Before tagging a release:
- [ ] All tests pass on release branch
- [ ] Security scan clean
- [ ] Coverage above production threshold (80%)
- [ ] CHANGELOG updated
- [ ] Version bumped in appropriate files
- [ ] Release notes prepared
