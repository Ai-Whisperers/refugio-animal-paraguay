# Agent Onboarding Guide

This document gives any AI agent a complete picture of the Refugio Animal Paraguay project so it can pick up work immediately. Read this first, then CLAUDE.md for behavioral rules.

---

## Quick Start

1. Read `.claude/CLAUDE.md` for behavioral rules and workflow commands
2. Check `tickets/current.md` for active work (if any)
3. Check `planning/` for the story queue — use `/next-story` to pick up work
4. Run tests: `PYTHONPATH=. python3 -m pytest tests/ -x -q`
5. Branch from `develop`, name branches `feature/RAP-NNN-description`

---

## Architecture Overview

```
                    ┌─────────────────┐
                    │   Traefik v3    │  (SSL, routing)
                    │  sunstein.cloud │
                    └──────┬──────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
    /petShelter/api/*          /petShelter/*
              │                         │
     ┌────────▼────────┐     ┌─────────▼─────────┐
     │   FastAPI API   │     │  Next.js Frontend  │
     │   (Python 3.12) │     │  (Node.js 14)      │
     │   Port 8000     │     │  Port 3000         │
     └────────┬────────┘     └───────────────────┘
              │
     ┌────────▼────────┐
     │  PostgreSQL 16  │
     │  (asyncpg)      │
     └─────────────────┘
```

### Backend Stack
- **Framework**: FastAPI with async SQLAlchemy 2.x ORM
- **Auth**: Custom JWT (python-jose + bcrypt), roles: `staff`, `admin`
- **Migrations**: Alembic (22 migrations, 001-019 with 008b, 012a, 012b, 012c)
- **Event Bus**: Custom domain event system (`src/events/`) with handlers for email, in-app, WhatsApp notifications
- **Middleware**: RequestID, AuditLog (all writes), CORS, Rate Limiting (slowapi)

### Frontend Stack
- **Framework**: Next.js 14 App Router, TypeScript
- **Styling**: Tailwind CSS with custom theme (primary: #E8622A, secondary: #2A7E62)
- **Data**: SWR for fetching, react-hook-form + zod for forms
- **Locale**: Spanish (es-PY), centralized strings in `frontend/src/lib/strings.ts`

---

## Source File Map

### Backend: `src/`

```
src/
├── app.py                     # FastAPI app factory, router registration, middleware stack
├── config.py                  # Pydantic Settings (DB, auth, email, Stripe, Tigo, WhatsApp)
│
├── api/                       # 27 API routers
│   ├── health.py              # GET /health
│   ├── auth.py                # POST /auth/token, /auth/users, GET /auth/me
│   ├── animals.py             # CRUD /animals + photos
│   ├── adopters.py            # CRUD /adopters (soft-delete)
│   ├── adoption_requests.py   # POST/GET /adoption-requests, status transitions, contracts
│   ├── donors.py              # POST/GET /donors
│   ├── donations.py           # POST /donations (Stripe), /donations/cash, stats, export
│   ├── in_kind_donations.py   # CRUD /in-kind-donations
│   ├── fund_allocations.py    # CRUD /fund-allocations + summary
│   ├── admin.py               # GET /admin/users, /admin/audit-logs
│   ├── admin_campaigns.py     # CRUD /admin/campaigns
│   ├── public.py              # GET /public/animals (no auth)
│   ├── public_adoption.py     # POST /public/adoption-applications (no auth)
│   ├── public_campaigns.py    # GET /public/campaigns (no auth)
│   ├── public_contact.py      # POST /public/contact, /public/animal-inquiry (no auth)
│   ├── sepa.py                # POST /donations/sepa, subscriptions
│   ├── tigo_money.py          # POST /tigo-money/payment-init, /tigo-money/webhook
│   ├── webhooks.py            # POST /webhooks/stripe
│   ├── consents.py            # GDPR consent CRUD
│   ├── notifications.py       # In-app notification CRUD
│   ├── notification_preferences.py  # Notification channel preferences
│   ├── gdpr_export.py         # POST /gdpr/data-export (Article 15/20)
│   ├── gdpr.py                # POST /gdpr/deletion-request (Article 17)
│   ├── follow_ups.py          # Post-adoption follow-up tracking
│   ├── impact_reports.py      # POST /impact-reports/generate
│   ├── sponsorships.py        # Full sponsorship lifecycle (tiers, create, pause, cancel)
│   └── animal_updates.py      # Sponsor update notifications
│
├── schemas/                   # Pydantic v2 request/response models (one file per domain)
│   ├── animal.py, adopter.py, adoption_request.py, donation.py, campaign.py
│   ├── sponsorship.py, follow_up.py, consent.py, notification.py, contact.py
│   ├── gdpr_export.py, gdpr_deletion.py, impact_report.py, tigo_money.py
│   ├── fund_allocation.py, in_kind_donation.py, animal_update.py
│   ├── public.py, public_adoption.py, audit.py, error.py, user.py
│   └── notification_preference.py
│
├── db/
│   ├── base.py                # SQLAlchemy DeclarativeBase
│   ├── session.py             # AsyncSession factory + engine lifecycle
│   ├── models/                # 21 SQLAlchemy ORM models
│   │   ├── animal.py          # Animal, AnimalPhoto
│   │   ├── adopter.py         # Adopter (soft-delete)
│   │   ├── adoption_request.py # AdoptionRequest (status lifecycle)
│   │   ├── user.py            # User (staff/admin roles)
│   │   ├── donor.py           # Donor
│   │   ├── donation.py        # Donation (multi-currency, multi-method)
│   │   ├── campaign.py        # Campaign, CampaignDonation
│   │   ├── sponsorship.py     # SponsorshipTier, Sponsorship
│   │   ├── user_consent.py    # UserConsent (GDPR)
│   │   ├── notification.py    # Notification
│   │   ├── notification_preference.py
│   │   ├── in_kind_donation.py
│   │   ├── fund_allocation.py
│   │   ├── contact_submission.py
│   │   ├── audit_log.py       # AuditLog
│   │   ├── follow_up.py       # FollowUp
│   │   ├── animal_update.py   # AnimalUpdate, SponsorUpdatePreference
│   │   └── __init__.py        # Re-exports all models
│   ├── alembic/
│   │   ├── env.py             # Alembic config (async, imports all models)
│   │   └── versions/          # 22 migration files (001-019 + 008b, 012a, 012b, 012c)
│   └── seeds/animals.py       # Seed data utilities
│
├── services/                  # Business logic layer
│   ├── consent_service.py     # GDPR consent operations
│   ├── notification_service.py # In-app notification CRUD
│   ├── notification_preference_service.py
│   ├── gdpr_export_service.py # Data export (Article 15/20)
│   ├── gdpr_deletion_service.py # Data erasure (Article 17)
│   ├── contract_service.py    # Adoption contract PDF (fpdf2)
│   ├── follow_up_service.py   # Post-adoption follow-up
│   ├── fund_allocation_service.py
│   ├── impact_report_service.py # Shelter metrics aggregation
│   ├── campaign_social_proof_service.py
│   ├── sponsor_update_service.py # Update dispatch to sponsors
│   └── tigo_money_service.py  # Tigo Money API integration
│
├── events/                    # Domain event system
│   ├── types.py               # DomainEvent base, EventType enum
│   ├── domain_events.py       # Concrete events + factory functions
│   ├── bus.py                 # EventBus (publish/subscribe)
│   └── dependencies.py        # get_event_bus() DI
│
├── notifications/             # Multi-channel notification delivery
│   ├── service.py             # Email (SMTP)
│   ├── templates.py           # Email templates
│   ├── handlers.py            # Email event subscribers
│   ├── in_app_handlers.py     # In-app notification subscribers
│   ├── whatsapp_service.py    # Twilio WhatsApp
│   └── whatsapp_handlers.py   # WhatsApp event subscribers
│
├── auth/
│   ├── dependencies.py        # require_staff(), require_admin(), get_current_user()
│   └── utils.py               # JWT creation/verification, password hashing
│
├── middleware/
│   ├── error_handler.py       # Consistent error responses
│   ├── rate_limiter.py        # slowapi (60/min general, 5/min auth)
│   └── request_id.py          # X-Request-ID header
│
└── audit/
    ├── middleware.py           # Captures POST/PATCH/DELETE with user context
    └── service.py             # AuditLog persistence
```

### Frontend: `frontend/src/`

```
frontend/src/
├── app/
│   ├── layout.tsx             # Root layout (Navbar, Footer, WhatsAppFab)
│   ├── page.tsx               # Homepage (hero, stats, CTAs)
│   ├── not-found.tsx          # Custom 404 (Spanish)
│   ├── animals/
│   │   ├── page.tsx           # Animal listing with filters (species, size, age, search)
│   │   └── [id]/
│   │       ├── page.tsx       # Animal detail (gallery, lightbox, WhatsApp CTA)
│   │       └── apply/page.tsx # 3-step adoption form (personal > home > GDPR consent)
│   ├── donate/
│   │   ├── page.tsx           # Donation hub (campaigns, bank details)
│   │   └── campaigns/[id]/page.tsx  # Campaign detail + donation form
│   ├── about/page.tsx         # About page
│   ├── volunteer/page.tsx     # Volunteer info
│   ├── foster/page.tsx        # Foster program
│   ├── stories/page.tsx       # Success stories
│   └── contact/page.tsx       # Contact form
│
├── components/
│   ├── Navbar.tsx             # Sticky header, mobile hamburger menu
│   ├── Footer.tsx             # Site footer
│   ├── WhatsAppFab.tsx        # Floating WhatsApp button
│   ├── DonationForm.tsx       # Multi-step donation (amount > details > submit)
│   ├── CampaignCard.tsx       # Campaign preview card
│   ├── CampaignListSection.tsx # Campaign grid with loading states
│   ├── CampaignDetailClient.tsx # Campaign page client component
│   ├── DynamicIcon.tsx        # Lucide icon mapper
│   ├── AnimalPlaceholder.tsx  # Species-specific SVG placeholder
│   └── AnimalCardSkeleton.tsx # Loading skeleton
│
├── lib/
│   ├── api.ts                 # HTTP client (get/post/put/patch/delete), JWT injection
│   ├── public-api.ts          # Public API functions (no auth required)
│   ├── auth.ts                # JWT token management (in-memory + sessionStorage)
│   ├── strings.ts             # All UI strings (Spanish), centralized
│   ├── animal-utils.ts        # Status labels, badge classes, age calculation
│   └── campaign-utils.ts      # Currency formatting, category icons/labels
│
├── types/
│   └── api.ts                 # TypeScript interfaces mirroring backend schemas
│
└── globals.css                # Tailwind config, CSS variables, accessibility
```

---

## Database Schema (21 tables)

| Table | Key Fields | Notes |
|-------|-----------|-------|
| `animals` | name, species, status, breed, size, gender, birth_date, primary_photo_url | Status lifecycle: intake > quarantine > available > foster > adopted > deceased |
| `animal_photos` | animal_id, url, caption, display_order | Cloudinary URLs |
| `adopters` | full_name, email, phone, gdpr_consent_at, deleted_at | Soft-delete for GDPR |
| `adoption_requests` | animal_id, adopter_id, status, contract_pdf_path | Status: pending > approved/rejected/cancelled |
| `users` | email, hashed_password, role | Roles: staff, admin |
| `donors` | full_name, email, country, currency_preference, show_in_public | EU + local donors |
| `donations` | donor_id, amount_cents, currency, payment_method, status | Money stored as integer cents |
| `campaigns` | title, target_amount_cents, fund_category, status, featured | Donation campaigns |
| `campaign_donations` | campaign_id, donation_id | Junction table |
| `sponsorship_tiers` | level (bronze/silver/gold), amount_cents, benefits (JSON) | 3 tiers |
| `sponsorships` | donor_id, animal_id, tier_id, status, frequency | Active/paused/cancelled |
| `user_consents` | user_id, consent_type, status, method | GDPR Article 7 |
| `notifications` | user_id, type, title, message, is_read | In-app notifications |
| `notification_preferences` | user_id, type, channel, enabled | Per-type opt-in/out |
| `in_kind_donations` | donor_id, item_type, quantity, estimated_value_cents | Non-cash donations |
| `fund_allocations` | category, amount_cents, description | Expense tracking |
| `contact_submissions` | form_type, visitor_name, visitor_email, message | Public forms |
| `audit_logs` | user_id, action, resource_type, old_values, new_values | GDPR Article 30 |
| `follow_ups` | adoption_request_id, scheduled_date, welfare_score | Post-adoption tracking |
| `animal_updates` | animal_id, title, content, update_type, photo_urls | Sponsor updates |
| `sponsor_update_preferences` | sponsorship_id, notification_frequency | Digest preferences |

All tables use UUID primary keys, TIMESTAMP(timezone=True), and money as integer cents.

---

## Alembic Migration Chain

```
001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 008b → 009 → 010 → 012 → 012a → 012b → 012c → 013 → 014 → 015 → 016 → 017 → 018 → 019
```

Migrations live in `src/db/alembic/versions/`. The chain was linearized from parallel branches — note the 008b and 012a/b/c naming.

---

## Test Structure

```
tests/
├── conftest.py               # Shared fixtures: make_animal_data(), make_adopter_data(),
│                              # make_donor_data(), frozen_now, rate limiter disable
├── unit/                      # 627 tests (54 files)
│   ├── conftest.py
│   ├── test_*_schemas.py      # Pydantic validation (13 files)
│   ├── test_*_service.py      # Business logic with mocked DB (11 files)
│   ├── test_auth_utils.py     # JWT/password utilities
│   ├── test_event_bus.py      # Event system (21 tests)
│   ├── test_models.py         # ORM model validation (30 tests)
│   └── test_webhooks.py       # Stripe webhook handlers
│
└── integration/               # 360 tests (28 files)
    ├── conftest.py            # Authenticated AsyncClient + EventBus fixture
    ├── test_animals.py        # Animal CRUD endpoints
    ├── test_adoption_requests.py  # Adoption workflow
    ├── test_donations.py      # Payment endpoints (Stripe mocked)
    ├── test_campaigns.py      # Campaign lifecycle (32 tests)
    ├── test_sponsorships.py   # Sponsorship lifecycle (30 tests)
    └── test_*.py              # One file per domain
```

**Running tests**: `PYTHONPATH=. python3 -m pytest tests/ -x -q`
**Unit only**: `PYTHONPATH=. python3 -m pytest tests/unit/ -q`
**Integration** (needs PostgreSQL): `PYTHONPATH=. python3 -m pytest tests/integration/ -q`
**Coverage**: `PYTHONPATH=. python3 -m pytest --cov=src --cov-report=term-missing`

---

## Deployment

### Live Site
- **URL**: https://sunstein.cloud/petShelter
- **API**: https://sunstein.cloud/petShelter/api/v1/
- **VPS**: Hostinger (Docker Compose + Traefik v3)

### Auto-Deploy
Push to `develop` triggers `.github/workflows/deploy.yml`:
1. SSH to VPS
2. `git fetch origin develop && git reset --hard origin/develop`
3. `docker compose -f docker-compose.deploy.yml build && up -d`
4. Health check

### Docker Services (docker-compose.deploy.yml)
- `db`: postgres:16-alpine (user: `refugio_user`, db: `refugio_prod`)
- `api`: Python/FastAPI (port 8000, auto-runs Alembic migrations on start)
- `frontend`: Next.js (port 3000)
- Traefik labels route `/petShelter/api` (priority 10) and `/petShelter` (priority 5)

### Admin Access
- Login: `POST /petShelter/api/v1/auth/token` with `{"username": "<email>", "password": "<pass>"}`
- Create admin user via SQL if none exists (see deployment notes)

---

## Known Issues (P0/P1)

1. **P0**: `/animals` page renders 404 content despite HTTP 200 — client-side hydration/data-fetch issue
2. **P0**: Tigo Money router registered in app.py but may need verification on prod
3. **P0**: No `error.tsx` boundary — unhandled errors crash the app
4. **P0**: DonationForm has no actual Stripe.js integration (form submits to API but no Stripe Elements)
5. **P1**: Backend has 60+ endpoints but frontend only uses ~8 of them
6. **P1**: `adoption_requests` test coverage at 41%, some new modules at 0%
7. **P1**: No loading states or error handling on several frontend pages
8. **P1**: Missing CSRF protection on mutation endpoints

---

## Roadmap Status

### Completed (V1-V3 + UX Sprint)
47 stories, 275 story points delivered. Covers: core CRUD, auth, photos, donations (Stripe + cash), SEPA, campaigns, sponsorships, GDPR (consent, export, deletion), notifications (in-app + email + WhatsApp), follow-ups, impact reports, Tigo Money, public portal, contact forms, campaign social proof, and the Next.js frontend scaffold.

### Not Started (V4-V13)
225 stories, 920 story points planned. Covers: medical records, volunteer management, admin dashboard, lost & found, foster program, advanced analytics, multi-shelter, PWA, i18n (Guarani), and more.

### Story Queue Location
- `planning/epics/EPIC-N-*/stories/S*-*/STORY.md` — individual story files
- `docs/EPICS.md` — epic overview
- `docs/roadmap/v1-mvp.md` through `v5-analytics-scale.md` — phase details

---

## Key Patterns for New Code

### Adding a new API endpoint
1. Create schema in `src/schemas/your_domain.py`
2. Create/update model in `src/db/models/your_model.py`
3. Add migration: `alembic revision --autogenerate -m "description"`
4. Create router in `src/api/your_router.py`
5. Register router in `src/app.py` (search for `app.include_router`)
6. Write unit tests in `tests/unit/test_your_schemas.py`
7. Write integration tests in `tests/integration/test_your_endpoint.py`

### Adding a frontend page
1. Create route in `frontend/src/app/your-page/page.tsx`
2. Add strings to `frontend/src/lib/strings.ts`
3. Add types to `frontend/src/types/api.ts`
4. Add API function to `frontend/src/lib/public-api.ts`
5. Add nav link to `frontend/src/components/Navbar.tsx`

### Event-driven notifications
1. Define event in `src/events/domain_events.py`
2. Add handler in `src/notifications/handlers.py` (email) or `in_app_handlers.py`
3. Publish from router: `event_bus.publish(create_your_event(...))`

---

## Environment Variables (Backend)

| Variable | Required | Purpose |
|----------|----------|---------|
| `DATABASE_URL` | Yes | PostgreSQL connection (must use `asyncpg://`) |
| `JWT_SECRET_KEY` | Yes | JWT signing key (min 32 chars) |
| `STRIPE_SECRET_KEY` | For payments | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | For webhooks | Stripe webhook signing secret |
| `TIGO_MONEY_API_KEY` | For Tigo | Tigo Money API key |
| `TWILIO_ACCOUNT_SID` | For WhatsApp | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | For WhatsApp | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | For WhatsApp | Twilio WhatsApp sender number |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | For email | SMTP server config |
| `CORS_ORIGINS` | Recommended | Allowed CORS origins (comma-separated) |

---

*Last updated: 2026-03-27*
