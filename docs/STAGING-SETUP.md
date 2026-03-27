# Staging Environment Setup

## Overview

The staging environment mirrors production but runs at a separate path on the same VPS.

| Environment | URL | Trigger |
|-------------|-----|---------|
| Staging | `https://sunstein.cloud/petShelter-staging` | Automatic on `develop` push |
| Production | `https://sunstein.cloud/petShelter` | Manual approval gate on `main` push |

---

## GitHub Environments (one-time setup)

Go to **Settings → Environments** in the GitHub repository and create two environments:

### staging
- No required reviewers
- No deployment branches restriction (allows `develop`)

### production
- Add **required reviewers** (at minimum: the repository owner)
- Restrict to `main` branch only
- This is the approval gate — every production deploy requires explicit sign-off

---

## VPS Secrets (GitHub Actions)

These secrets must be set in **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `VPS_SSH_KEY` | Private SSH key for deploy user |
| `VPS_KNOWN_HOSTS` | Output of `ssh-keyscan <VPS_HOST>` |
| `VPS_USER` | SSH user on VPS (e.g. `deploy`) |
| `VPS_HOST` | VPS hostname (e.g. `sunstein.cloud`) |

---

## VPS Environment Files

On the VPS at `/opt/refugio-animal-paraguay/`, create:

### `.env.staging`
```
POSTGRES_PASSWORD_STAGING=<random secure password — different from production>
SECRET_KEY_STAGING=<random 64-char hex string — different from production>
STRIPE_SECRET_KEY=sk_test_<your Stripe test key>
STRIPE_WEBHOOK_SECRET=whsec_<staging webhook secret>
```

### `.env` (production — already exists)
```
POSTGRES_PASSWORD=<production DB password>
SECRET_KEY=<production signing key>
STRIPE_SECRET_KEY=sk_live_<production Stripe key>
STRIPE_WEBHOOK_SECRET=whsec_<production webhook secret>
```

Docker Compose reads the relevant `.env` file automatically based on the `--env-file` flag
or by default from `.env` in the working directory. To use staging vars:

```bash
docker compose --env-file .env.staging -f docker-compose.staging.yml up -d
```

---

## Deploy Flow

```
develop branch push
        │
        ▼
  staging.yml runs
        │
        ▼
Auto-deploy to staging (no approval needed)
        │
        ▼
Manual testing on sunstein.cloud/petShelter-staging
        │
        ▼
PR: develop → main (code review)
        │
        ▼
Merge to main triggers deploy.yml
        │
        ▼
GitHub waits for required reviewer approval (production environment gate)
        │
        ▼
Reviewer approves → production deploy runs
        │
        ▼
sunstein.cloud/petShelter updated
```

---

## Staging Database

The staging database (`refugio_staging`) is isolated from production (`refugio_prod`).
Both run on the same VPS as separate PostgreSQL containers.

To seed staging with test data after first deploy:
```bash
ssh user@sunstein.cloud
cd /opt/refugio-animal-paraguay
docker compose -f docker-compose.staging.yml exec api-staging \
  python -m src.db.seed  # if seed script exists
```

---

## Rollback

**Staging**: Just push a fix commit to `develop`.

**Production**: Use `workflow_dispatch` from the Actions tab — specify the previous
working SHA or branch in the `ref` input field.
