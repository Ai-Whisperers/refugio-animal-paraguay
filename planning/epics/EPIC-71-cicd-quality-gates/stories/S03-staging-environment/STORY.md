---
story: S03
epic: EPIC-71
ticket: RAP-402
title: "Create staging environment with approval gate"
status: ready
points: 5
priority: P1
track: DevOps
sprint: priority
version: V3.1
created: 2026-03-27
---

# S03: Create staging environment with approval gate

## Story
As a **developer**, I want **a staging environment that mirrors production** so that **I can verify deployments before they reach real users**.

## Description
Create a staging deployment target on the same VPS using a separate Docker Compose profile. The staging environment runs on a different port/path and uses a separate database. Deploy to staging automatically on push to `develop`. Deploy to production only on manual approval or tag push.

## Acceptance Criteria

**Given** a push to the `develop` branch
**When** tests pass in CI
**Then** the application deploys to staging at `sunstein.cloud/petShelter-staging`

**Given** a staging deployment succeeds
**When** a developer manually approves in GitHub Actions
**Then** the same commit deploys to production at `sunstein.cloud/petShelter`

- [ ] Staging uses separate database (`refugio_staging`)
- [ ] Staging has its own Traefik labels for routing
- [ ] Production deploy requires manual approval via GitHub Actions environment protection rules
- [ ] Staging health check passes before production deploy is offered

## Definition of Done
- [ ] `docker-compose.staging.yml` created (or staging profile in existing compose)
- [ ] Traefik labels for staging path configured
- [ ] Staging database created and migrations run automatically
- [ ] GitHub Actions workflow updated: test → staging deploy → approval gate → production deploy
- [ ] Staging environment accessible and tested

## Technical Notes
- Epic: EPIC-71
- Track: DevOps
- Priority: P1
- VPS: Same Hostinger VPS, different Docker Compose project name
- Staging URL: `sunstein.cloud/petShelter-staging` or similar
- GitHub environments: Create `staging` and `production` environments with protection rules

## Story Points: 5
