# V1 — MVP: Core Shelter Operations

**Version**: 1.0.0
**Timeline**: 4-6 weeks
**Status**: ~65% backend complete, 0% frontend
**Theme**: *"Staff can manage animals and process adoptions through a working system"*

---

## Goal

Deliver a functional animal shelter management system where staff can register animals, process adoption requests, and manage basic operations. A minimal public-facing portal lets adopters browse animals and submit applications. This is the first version shown to the client and EU funders.

---

## What's Already Built

| Component | Ticket | Status |
|-----------|--------|--------|
| PostgreSQL schema (animals, adopters, requests) | RAP-001 | Done |
| SQLAlchemy ORM models | RAP-002 | Done |
| FastAPI scaffold + health check | RAP-003 | Done |
| Animal CRUD API (paginated, filtered) | RAP-004 | Done |
| Adopter CRUD API (soft-delete, GDPR) | RAP-005 | Done |
| Adoption request API (state machine) | RAP-006 | Done |
| JWT auth + role-based access | RAP-007 | Done |
| Animal photo gallery | RAP-008 | Done |
| Stripe donation foundation | RAP-009 | Done |
| Docker containerization | RAP-010 | Done |

---

## What V1 Adds

### 1. Public Portal Frontend (New — EPIC-11 partial)

The biggest V1 deliverable. A minimal web frontend for public users.

| Feature | Description | Priority |
|---------|-------------|----------|
| Animal browsing page | Grid/list view with species + status filters | P0 |
| Animal detail page | Photos, description, status, "Apply to Adopt" button | P0 |
| Adoption application form | Name, email, phone, motivation — submits to existing API | P0 |
| Application status check | Adopter enters email to see their application status | P1 |
| Responsive layout | Mobile-first — most adopters in Paraguay use phones | P0 |

**Tech stack**: Next.js 14 (App Router) + Tailwind CSS + TypeScript
**Hosting**: Vercel (free tier) or self-hosted via Docker

### 2. Staff Admin Panel (New — EPIC-7 partial)

Minimal admin interface for shelter staff. Not a full dashboard — just operational CRUD.

| Feature | Description | Priority |
|---------|-------------|----------|
| Animal management | Add/edit/remove animals with photo upload | P0 |
| Adoption queue | View pending requests, approve/reject with one click | P0 |
| Adopter list | Search adopters, view history | P1 |
| Login page | Email + password auth using existing JWT | P0 |

### 3. CI/CD Pipeline (EPIC-9)

| Feature | Description | Priority |
|---------|-------------|----------|
| GitHub Actions workflow | Lint, type-check, test on every PR | P0 |
| Docker image build | Build + push to GitHub Container Registry | P1 |
| Staging deployment | Auto-deploy `develop` branch to staging | P1 |

### 4. Auth Completion (EPIC-10 partial)

| Feature | Description | Priority |
|---------|-------------|----------|
| Password reset flow | Time-limited token via email | P1 |
| Email verification | Verify new accounts before activation | P2 |

### 5. API Hardening

| Feature | Description | Priority |
|---------|-------------|----------|
| Rate limiting | Public endpoints: 60 req/min per IP | P1 |
| CORS configuration | Allow frontend origin only | P0 |
| Error response standardization | Consistent error schema across all endpoints | P1 |
| Request validation improvements | Better error messages for invalid input | P2 |

---

## Acceptance Criteria

V1 is complete when:

- [ ] Public user can browse available animals on the website
- [ ] Public user can view animal details with photos
- [ ] Public user can submit an adoption application
- [ ] Staff can log in to the admin panel
- [ ] Staff can add/edit animals with photos
- [ ] Staff can approve or reject adoption requests
- [ ] Adoption approval changes animal status to "adopted"
- [ ] CI pipeline runs on every PR (lint + type-check + tests)
- [ ] Docker image builds and deploys to staging
- [ ] All existing 204 tests still pass
- [ ] New frontend has basic test coverage (>60%)
- [ ] System runs on a single server with Docker Compose

---

## What V1 Does NOT Include

- Donation processing UI (API exists, no frontend yet)
- Email/WhatsApp notifications
- Volunteer management
- Medical records
- Advanced search
- Production hosting with TLS (staging only)
- Multi-language support (Spanish/Guarani)

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Frontend delays (new codebase) | V1 slips past 6 weeks | Start with server-rendered pages, add interactivity later |
| No designer available | UI looks unprofessional for client demo | Use Tailwind UI components, focus on clean data display |
| Staging server costs | Budget concern for Paraguay context | Use free tiers (Vercel, Railway) or single VPS |
| Auth flows need email | Email provider not yet chosen | Use console logging in staging, wire real email in V2 |

---

## Estimated Effort

| Area | New Tickets | Story Points | Weeks |
|------|-------------|-------------|-------|
| Frontend (public portal) | 4-5 | 13-15 | 2-3 |
| Staff admin panel | 3-4 | 8-10 | 1.5-2 |
| CI/CD pipeline | 2 | 5 | 0.5-1 |
| Auth completion | 2 | 5 | 0.5-1 |
| API hardening | 2-3 | 5 | 0.5 |
| **Total** | **13-16** | **36-40** | **5-7** |

---

## Demo Script (Client Presentation)

1. Open the public website — show animal grid with photos
2. Click an animal — show detail page with gallery
3. Submit an adoption application — show the form
4. Log in as staff — show admin panel
5. Review the application — approve it
6. Show the animal status changed to "adopted"
7. Show the health check endpoint and CI pipeline running

*"This is the core loop. Every feature we add from V2 onward builds on this foundation."*

---

## Dependencies

- **Blocks V2**: Donation UI needs the frontend from V1
- **Blocks V3**: Notifications need the CI/CD pipeline from V1
- **External**: Domain name registration, hosting account setup

---

*Epics touched: EPIC-7 (partial), EPIC-9, EPIC-10 (partial), EPIC-11 (partial)*
*Target release tag: `v1.0.0`*
