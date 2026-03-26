# Refugio Animal Paraguay — Product Roadmap

**Last updated**: 2026-03-26
**Total versions**: 5 (MVP → Production-ready)
**Total timeline**: ~24 weeks (6 months)
**Current state**: Phase 2 complete — backend APIs, auth, Docker, 204 tests passing

---

## Version Overview

| Version | Theme | Timeline | Key Deliverable |
|---------|-------|----------|----------------|
| **[V1 — MVP](v1-mvp.md)** | Core Shelter Operations | Weeks 1-4 | Staff manages animals + adoptions; public portal |
| **[V2 — Donations](v2-donations-payments.md)** | EU Payment Integration | Weeks 5-8 | EU donors contribute via Stripe + SEPA |
| **[V3 — Communications](v3-communications.md)** | Notifications & Workflow | Weeks 9-12 | Email + WhatsApp; adoption contracts; local payments |
| **[V4 — Operations](v4-operations.md)** | Volunteers, Medical, Foster | Weeks 13-18 | Full shelter operations digitized |
| **[V5 — Analytics](v5-analytics-scale.md)** | Dashboard & Scale | Weeks 19-24 | Funder reporting; production hardening |

---

## What's Already Built (Pre-V1)

The backend foundation is complete. 10 tickets delivered (RAP-001 through RAP-010):

| Layer | Status | Details |
|-------|--------|---------|
| Database schema | Done | PostgreSQL 16, 4 Alembic migrations, 6 ORM models |
| REST API | Done | 7 routers, full CRUD for animals/adopters/adoptions/donors/donations |
| Authentication | Done | JWT bearer tokens, role-based access (admin/staff) |
| Photo management | Done | Animal photo gallery with upload/delete |
| Stripe foundation | Done | PaymentIntent creation, test mode |
| Docker | Done | Multi-stage build, Compose with auto-migrations |
| Tests | Done | 204 tests (96 unit + 108 integration), zero failures |

---

## Cumulative Feature Matrix

This table shows what's available to each user role at each version:

| Capability | V1 | V2 | V3 | V4 | V5 |
|-----------|:--:|:--:|:--:|:--:|:--:|
| Browse animals online | x | x | x | x | x |
| Submit adoption application | x | x | x | x | x |
| Check application status | x | x | x | x | x |
| Staff animal management | x | x | x | x | x |
| Staff adoption review | x | x | x | x | x |
| CI/CD pipeline | x | x | x | x | x |
| Online card donations | | x | x | x | x |
| SEPA recurring donations | | x | x | x | x |
| Donation dashboard | | x | x | x | x |
| GDPR compliance | | x | x | x | x |
| Audit trail | | x | x | x | x |
| Animal sponsorship | | x | x | x | x |
| Fundraising campaigns | | x | x | x | x |
| In-kind donation tracking | | x | x | x | x |
| Email notifications | | | x | x | x |
| WhatsApp notifications | | | x | x | x |
| Adoption contracts (PDF) | | | x | x | x |
| Post-adoption follow-up | | | x | x | x |
| Local PYG payments | | | x | x | x |
| Multi-language (ES/EN) | | | x | x | x |
| Impact report generator | | | x | x | x |
| Fund allocation tracking | | | x | x | x |
| Volunteer management | | | | x | x |
| Medical records | | | | x | x |
| Foster program | | | | x | x |
| Outcome metrics | | | | x | x |
| Admin analytics dashboard | | | | | x |
| Funder-specific dashboards | | | | | x |
| Full-text search | | | | | x |
| 2FA authentication | | | | | x |
| E2E test suite | | | | | x |

---

## Epic Completion by Version

| Epic | V1 | V2 | V3 | V4 | V5 |
|------|:--:|:--:|:--:|:--:|:--:|
| EPIC-0: Testing Foundation | partial | partial | partial | partial | **complete** |
| EPIC-1: Animal Catalog | 90% | 90% | 90% | 95% | **complete** |
| EPIC-2: Adoption Workflow | 50% | 50% | **complete** | complete | complete |
| EPIC-3: Donations & Payments | 40% | 80% | **complete** | complete | complete |
| EPIC-4: Medical Records | 0% | 0% | 0% | **complete** | complete |
| EPIC-5: Volunteer Management | 0% | 0% | 0% | **complete** | complete |
| EPIC-6: Communications | 0% | partial | **complete** | complete | complete |
| EPIC-7: Admin Dashboards | partial | partial | partial | partial | **complete** |
| EPIC-8: QA & Testing | partial | partial | partial | partial | **complete** |
| EPIC-9: Infrastructure | 70% | 90% | 90% | 95% | **complete** |
| EPIC-10: Auth & Accounts | 50% | 50% | 50% | 60% | **complete** |
| EPIC-11: Public Portal | 0% | partial | partial | partial | **complete** |
| EPIC-12: Foster Program | 0% | 0% | 0% | **complete** | complete |
| EPIC-13: Impact & Compliance | 0% | partial | partial | partial | **complete** |
| EPIC-14: Sponsorship & Campaigns | 0% | partial | **complete** | complete | complete |

---

## Effort Summary

| Version | New Tickets | Story Points | Weeks | Cumulative |
|---------|-------------|-------------|-------|-----------|
| V1 — MVP | 13-16 | 36-40 | 4-6 | 4-6 weeks |
| V2 — Donations | 12-15 | 38-43 | 4-6 | 8-12 weeks |
| V3 — Communications | 15-19 | 49-56 | 6-8 | 14-20 weeks |
| V4 — Operations | 17-22 | 53-65 | 8-10 | 22-30 weeks |
| V5 — Analytics | 20-24 | 64-77 | 9-13 | 31-43 weeks |
| **Total** | **~96-118** | **~310-380** | **~33-47** | — |

> Note: Weeks assume a single developer. With parallel work on frontend + backend, timelines compress to ~60-70%. V1-V3 are realistic as sequential sprints. V4 and V5 can overlap. Totals updated to include EPIC-12 (Foster), EPIC-13 (Impact/Compliance), and EPIC-14 (Sponsorship/Campaigns).

---

## Priority Rules

1. **Revenue-enabling features first** — V2 donation flow unlocks EU funding
2. **Communication before complexity** — V3 notifications make V4 operational features useful
3. **Staff adoption before public polish** — Staff must use the system before we optimize the public experience
4. **Hardening last** — Production scale in V5 after features stabilize
5. **Each version is demo-ready** — Every release can be shown to the client with a clear narrative

---

## Decision Log

| Decision | Rationale | Version |
|----------|-----------|---------|
| Next.js 14 for frontend | App Router, server components, Vercel deployment | V1 |
| Stripe for EU payments | Best SEPA support, developer experience, PCI compliance | V2 |
| Resend for email | EU data processing, developer-friendly API | V2 |
| WhatsApp over SMS | Paraguay market: WhatsApp penetration >90%, SMS declining | V3 |
| weasyprint for PDFs | Python-native, HTML templates, no external service | V3 |
| PostgreSQL tsvector over Elasticsearch | One less service to manage, sufficient for our scale | V5 |
| Redis for caching + pub/sub | Already in Docker stack, dual-purpose | V5 |
| Audit trail before donations | EU compliance requires accountability from day one | V2 |
| Sponsorship as recurring donation extension | Reuse Stripe subscription, not separate system | V2 |
| Foster as separate epic (EPIC-12) | Distinct lifecycle from adoption, own data models | V4 |

---

## Additional Documents

| Document | Purpose |
|----------|---------|
| [Epic Analysis & Improvements](epic-analysis-and-improvements.md) | Gap analysis, data quality issues, industry comparison |
| [Dependency Map & Priority Matrix](dependency-map.md) | Build order, parallel work streams, risk-weighted priorities |

---

## How to Use This Roadmap

**For development**: Each version file contains acceptance criteria and estimated tickets. Use `/create-story` to generate stories from the feature tables.

**For client demos**: Each version file includes a Demo Script section with a step-by-step walkthrough.

**For sprint planning**: Use the Effort Summary and Estimated Effort tables per version to plan 2-week sprints.

**For funder presentations**: The Cumulative Feature Matrix shows value delivery over time.

---

## File Index

```
docs/roadmap/
├── README.md                    ← This file (overview + matrices)
├── v1-mvp.md                    ← V1: Core shelter operations
├── v2-donations-payments.md     ← V2: EU donation integration
├── v3-communications.md         ← V3: Notifications + workflow completion
├── v4-operations.md             ← V4: Volunteers, medical, foster
└── v5-analytics-scale.md        ← V5: Dashboard, search, production scale
```

---

*Maintained by the development team. Update after each version release.*
