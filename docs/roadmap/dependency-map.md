# Epic Dependency Map & Priority Matrix

**Date**: 2026-03-26
**Epics**: 15 (EPIC-0 through EPIC-14)
**Stories**: 72 | **Estimated Points**: ~340

---

## Dependency Graph

```
                    ┌─────────────┐
                    │   EPIC-9    │
                    │ Infra/CI/CD │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  EPIC-10    │
                    │    Auth     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐    │     ┌──────▼──────┐
       │   EPIC-1    │    │     │  EPIC-11    │
       │   Animals   │    │     │   Portal    │
       └──────┬──────┘    │     └──────┬──────┘
              │            │            │
    ┌─────────┼─────┐     │     ┌──────┘
    │         │     │     │     │
┌───▼───┐ ┌──▼──┐ ┌▼─────▼─┐ ┌▼────────┐
│EPIC-2 │ │EP-4 │ │ EPIC-3  │ │ EPIC-14 │
│Adopt  │ │Med  │ │Donation │ │Sponsor  │
└───┬───┘ └──┬──┘ └────┬───┘ └────┬────┘
    │        │         │          │
    │    ┌───┘    ┌────┘     ┌────┘
    │    │        │          │
┌───▼────▼───┐  ┌▼──────────▼──┐
│   EPIC-6   │  │   EPIC-13    │
│  Comms/    │  │   Impact &   │
│  Notify    │  │  Compliance  │
└─────┬──────┘  └──────┬───────┘
      │                │
┌─────▼──────┐         │
│   EPIC-5   │         │
│ Volunteers │         │
└─────┬──────┘         │
      │                │
┌─────▼──────┐         │
│  EPIC-12   │         │
│   Foster   │         │
└─────┬──────┘         │
      │                │
      └───────┬────────┘
              │
       ┌──────▼──────┐
       │   EPIC-7    │
       │  Dashboard  │
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │   EPIC-8    │
       │     QA      │
       └─────────────┘
```

---

## Build Order (Critical Path)

### Layer 0 — Foundation (already done)
EPIC-9 (Docker) + EPIC-10 (Auth) + EPIC-1 (Animals) — *delivered via RAP-001 through RAP-010*

### Layer 1 — V1 MVP (weeks 1-4)
- EPIC-11 (Public Portal — frontend)
- EPIC-9 (CI/CD pipeline — remaining)
- EPIC-7 (Staff admin panel — minimal)

### Layer 2 — V2 Revenue (weeks 5-8)
- EPIC-3 (Donations — complete Stripe + SEPA)
- EPIC-13 S01-S02 (Audit trail + GDPR — required before accepting EU money)
- EPIC-14 S01, S03, S05 (Sponsorship tiers + campaigns + in-kind)
- EPIC-6 S01 (Email notifications — donation receipts)

### Layer 3 — V3 Communication (weeks 9-12)
- EPIC-6 (complete — WhatsApp, in-app, preferences)
- EPIC-2 (complete — contracts, notifications, follow-up)
- EPIC-13 S03-S04 (Impact reports + fund allocation)
- EPIC-14 S02, S04 (Sponsor updates + campaign progress)

### Layer 4 — V4 Operations (weeks 13-18)
- EPIC-4 (Medical records)
- EPIC-5 (Volunteers)
- EPIC-12 (Foster program)
- EPIC-13 S05 (Outcome metrics)

### Layer 5 — V5 Scale (weeks 19-24)
- EPIC-7 (Dashboard — complete with analytics)
- EPIC-8 (QA — E2E, performance, security)
- EPIC-1 (Search — tsvector, syndication)
- EPIC-10 (2FA, session management)

---

## Priority Matrix

### P0 — Must Have (MVP blockers)

| Epic | Story | Reason |
|------|-------|--------|
| EPIC-11 | S01: Animal Browsing | Users need to see animals |
| EPIC-11 | S05: Mobile-First Design | 85%+ Paraguay users on mobile |
| EPIC-9 | S02: CI/CD Pipeline | Quality gate for all future work |
| EPIC-7 | S01: Staff Admin (minimal) | Staff must manage daily operations |

### P0 — Must Have (Revenue blockers)

| Epic | Story | Reason |
|------|-------|--------|
| EPIC-3 | S01: Stripe Complete | Accept EU card payments |
| EPIC-3 | S02: SEPA Direct Debit | Recurring EU donor payments |
| EPIC-13 | S01: Audit Trail | Legal requirement before EU donations |
| EPIC-13 | S02: GDPR Compliance | Legal requirement for EU data |
| EPIC-14 | S01: Sponsorship Tiers | Highest-retention revenue model |

### P1 — Should Have (Engagement drivers)

| Epic | Story | Reason |
|------|-------|--------|
| EPIC-6 | S01: Email System | Donation receipts, adoption updates |
| EPIC-6 | S02: WhatsApp | Primary channel in Paraguay |
| EPIC-2 | S03: Adoption Notifications | Close the loop with adopters |
| EPIC-2 | S04: PDF Contracts | Formalize adoptions |
| EPIC-14 | S03: Campaigns | Emergency fundraising capability |
| EPIC-11 | S06: Success Stories | Drives donations + adoptions |

### P2 — Nice to Have (Operational efficiency)

| Epic | Story | Reason |
|------|-------|--------|
| EPIC-4 | All | Medical tracking improves care |
| EPIC-5 | All | Volunteer coordination reduces chaos |
| EPIC-12 | All | Capacity multiplier |
| EPIC-13 | S03: Impact Reports | Funder retention |
| EPIC-7 | S04: Reporting & Export | Operational visibility |

### P3 — Future (Scale & Polish)

| Epic | Story | Reason |
|------|-------|--------|
| EPIC-1 | S05: Full-text Search | Performance at scale |
| EPIC-1 | S09: PetFinder Syndication | Expanded reach |
| EPIC-8 | S03: E2E Tests | Quality at scale |
| EPIC-7 | S05: Capacity Census | Predictive operations |
| EPIC-10 | 2FA | Security hardening |

---

## Version-to-Epic Mapping (Updated with New Epics)

| Version | Epics (Primary) | Epics (Partial) | New Stories |
|---------|----------------|-----------------|-------------|
| **V1** | EPIC-11, EPIC-9 | EPIC-7, EPIC-10 | 13-16 |
| **V2** | EPIC-3, EPIC-14 | EPIC-6, EPIC-13 | 14-17 |
| **V3** | EPIC-6, EPIC-2 | EPIC-13, EPIC-14, EPIC-11 | 15-19 |
| **V4** | EPIC-4, EPIC-5, EPIC-12 | EPIC-13 | 17-22 |
| **V5** | EPIC-7, EPIC-8 | EPIC-1, EPIC-10, EPIC-11 | 20-24 |

---

## Cross-Cutting Concerns Timeline

| Concern | V1 | V2 | V3 | V4 | V5 |
|---------|:--:|:--:|:--:|:--:|:--:|
| Event bus | — | in-process | expand | expand | Redis |
| Notification dispatch | — | email only | +WhatsApp, in-app | +shift reminders | +WebSocket |
| Audit trail | — | foundation | expand | expand | viewer UI |
| File storage | local | local | S3/CDN | expand | optimize |
| PDF generation | — | — | contracts | medical docs | impact reports |
| Search | basic SQL | basic SQL | basic SQL | basic SQL | tsvector |
| Multi-language | — | — | ES + EN | expand | +Guarani |
| Export (CSV/PDF) | — | CSV | +PDF | expand | full reporting |
| Caching | — | — | — | — | Redis |

---

## Risk-Weighted Priority

Features sorted by (impact x probability of blocking launch) / effort:

| Rank | Feature | Impact | Effort | Risk Score |
|------|---------|--------|--------|-----------|
| 1 | Public animal browsing (EPIC-11 S01) | 10 | 5 | 20.0 |
| 2 | Stripe completion + webhooks (EPIC-3 S01) | 10 | 8 | 12.5 |
| 3 | GDPR consent tracking (EPIC-13 S02) | 9 | 6 | 15.0 |
| 4 | Audit trail (EPIC-13 S01) | 9 | 7 | 12.9 |
| 5 | Staff admin panel (EPIC-7 S01 minimal) | 9 | 8 | 11.3 |
| 6 | CI/CD pipeline (EPIC-9 S02) | 8 | 5 | 16.0 |
| 7 | SEPA Direct Debit (EPIC-3 S02) | 8 | 8 | 10.0 |
| 8 | Sponsorship tiers (EPIC-14 S01) | 8 | 8 | 10.0 |
| 9 | Email notifications (EPIC-6 S01) | 7 | 5 | 14.0 |
| 10 | Adoption contracts (EPIC-2 S04) | 7 | 6 | 11.7 |

---

## Parallel Work Streams

For a 2-person team (backend + frontend), these can run simultaneously:

| Sprint | Backend | Frontend |
|--------|---------|----------|
| V1 Sprint 1 | CI/CD pipeline, API hardening | Animal browsing page, mobile layout |
| V1 Sprint 2 | Rate limiting, CORS, auth fixes | Adoption form, staff login, admin CRUD |
| V2 Sprint 1 | Stripe webhooks, SEPA, audit trail | Donation landing page, payment form |
| V2 Sprint 2 | Sponsorship backend, GDPR endpoints | Sponsorship UI, campaign pages |
| V3 Sprint 1 | Email + WhatsApp engine | Notification preferences, success stories |
| V3 Sprint 2 | PDF contracts, adoption completion | Contact form, multi-language |
| V4 Sprint 1 | Medical records schema + API | Volunteer registration, shift calendar |
| V4 Sprint 2 | Foster program backend | Medical timeline UI, foster check-in |
| V5 Sprint 1 | tsvector search, Redis caching | Dashboard charts, KPI cards |
| V5 Sprint 2 | Impact report generator, E2E tests | Funder dashboards, export UI |

---

*This document should be updated as epics are completed and priorities shift.*
