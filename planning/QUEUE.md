# Development Queue — Refugio Animal Paraguay

**Last updated**: 2026-03-26
**Active version**: V2/V3 (completing remaining stories)
**Full roadmap**: [ROADMAP.md](ROADMAP.md) — 10 sprints, 50 epics, 250 stories
**Tech stack**: Python 3.12, FastAPI, SQLAlchemy 2.x, PostgreSQL 16, Next.js 14

---

## How This Queue Works

Stories are ordered by dependency and priority. Work top-to-bottom. Each story becomes a ticket when started (`/start-ticket RAP-NNN`). A story is "ready" when all its dependencies are met.

**Status**: DONE = delivered | READY = can start now | BLOCKED = waiting on dependency

---

## Already Delivered (RAP-001 through RAP-010)

| Story | Epic | Ticket | What was built |
|-------|------|--------|---------------|
| Animal Data Model & Schema | EPIC-1 S01 | RAP-001, RAP-002 | PostgreSQL schema, 6 ORM models, 4 migrations |
| Animal CRUD API | EPIC-1 S02-S03 | RAP-003, RAP-004 | 7 endpoints, pagination, filters |
| Photo Upload & Management | EPIC-1 S04 | RAP-008 | Photo gallery, upload/delete |
| Adopter CRUD API | EPIC-2 | RAP-005 | Soft-delete, GDPR consent tracking |
| Adoption Request API | EPIC-2 S01-S02 | RAP-006 | State machine, status transitions |
| JWT Auth + RBAC | EPIC-10 S01, S04 | RAP-007 | Login, roles (admin/staff/adopter) |
| Stripe Foundation | EPIC-3 S01 (partial) | RAP-009 | PaymentIntent, donor/donation models |
| Docker Setup | EPIC-9 S01 | RAP-010 | Multi-stage build, Compose, auto-migrations |

**Delivered**: 30 source files, 204 tests (96 unit + 108 integration), 80.42% coverage

---

## V1 — MVP Sprint Queue

### Sprint 1 (Weeks 1-2): Foundation + Frontend Start

| # | Story | Epic | Points | Status | Track |
|---|-------|------|--------|--------|-------|
| 1 | CI/CD Pipeline (GitHub Actions) | EPIC-9 S02 | 8 | DONE (PR #2) | Backend |
| 2 | Animal Intake Workflow | EPIC-1 S06 | 8 | DONE (PR #3) | Backend |
| 3 | CORS + Rate Limiting + Error Standardization | Cross-cutting | 5 | DONE (PR #13) | Backend |
| 4 | Next.js 14 Project Scaffold | EPIC-11 | 5 | DONE (PR #19) | Frontend |
| 5 | Animal Browsing Page (public) | EPIC-11 S01 | 8 | DONE (PR #20) | Frontend |

### Sprint 2 (Weeks 3-4): Admin Panel + Polish

| # | Story | Epic | Points | Status | Track |
|---|-------|------|--------|--------|-------|
| 6 | Staff Admin Panel — Animals + Adoptions | EPIC-7 S01 (partial) | 8 | DONE (PR #21) | Frontend |
| 7 | Adoption Application Form (public) | EPIC-11 S01 | 5 | DONE (PR #22) | Frontend |
| 8 | Mobile-First Responsive Design | EPIC-11 S05 | 5 | DONE (PR #23) | Frontend |
| 9 | Password Reset Flow | EPIC-10 S02 (partial) | 5 | DONE (PR #12) | Backend |
| 10 | Contact & Inquiry Form | EPIC-11 S02 | 8 | DONE (PR #24) | Frontend |

**V1 complete**: All 10 stories delivered. 65 points total.

### Parallel Tracks

```
Week 1-2:
  Backend:  #1 CI/CD → #2 Intake → #3 API Hardening
  Frontend: #4 Scaffold → #5 Animal Browsing

Week 3-4:
  Backend:  #9 Password Reset → V2 prep (event bus, audit trail)
  Frontend: #6 Admin Panel → #7 Adoption Form → #8 Mobile → #10 Contact
```

---

## V2 — Donations & EU Payments (Weeks 5-8)

| # | Story | Epic | Points | Status |
|---|-------|------|--------|--------|
| 1 | Event Bus Infrastructure | EPIC-9 S05 | 8 | DONE (PR #14) |
| 2 | Audit Trail System | EPIC-13 S01 | 7 | DONE (PR #15) |
| 3 | Stripe Webhook Processing | EPIC-3 S01 (remaining) | 8 | DONE (PR #25) |
| 4 | SEPA Direct Debit | EPIC-3 S02 | 8 | DONE (PR #53) |
| 5 | GDPR Consent Tracking | EPIC-13 S07 | 5 | DONE (PR #26) |
| 6 | Cash Donation Recording | EPIC-3 S06 | 3 | DONE (PR #16) |
| 7 | In-Kind Donation Recording | EPIC-14 S05 | 5 | DONE (PR #17) |
| 8 | Sponsorship Tiers & Matching | EPIC-14 S01 | 8 | DONE (PR #54) |
| 9 | Campaign Management | EPIC-14 S03 | 6 | READY |
| 10 | Donation Landing Page | EPIC-11 S04 | 13 | DONE (PR #51) |
| 11 | Donation Dashboard (Staff) | EPIC-3 S04 | 6 | READY |
| 12 | Email Notification System | EPIC-6 S01 | 8 | DONE (PR #18) |
| 13 | GDPR Data Export | EPIC-13 S02 | 6 | DONE (PR #48) |

---

## V3 — Communications (Weeks 9-12)

| # | Story | Epic | Points | Status |
|---|-------|------|--------|--------|
| 1 | WhatsApp Integration | EPIC-6 S02 | 8 | READY |
| 2 | In-App Notifications | EPIC-6 S03 | 6 | DONE (PR #32) |
| 3 | Notification Preferences | EPIC-6 S04 | 5 | DONE (PR #34) |
| 4 | Adoption Notifications (status changes) | EPIC-2 S03 | 5 | DONE (PR #39) |
| 5 | PDF Adoption Contracts | EPIC-2 S04 | 6 | DONE (PR #43) |
| 6 | Post-Adoption Follow-up | EPIC-2 S05 | 8 | DONE (PR #44) |
| 7 | Tigo Money Integration (PYG) | EPIC-3 S03 | 8 | READY |
| 8 | Sponsor Update Notifications | EPIC-14 S02 | 6 | READY |
| 9 | Campaign Progress & Social Proof | EPIC-14 S04 | 5 | READY |
| 10 | Impact Report Generator | EPIC-13 S03 | 7 | DONE (PR #50) |
| 11 | Fund Allocation Tracking | EPIC-13 S04 | 6 | DONE (PR #45) |
| 12 | GDPR Data Deletion | EPIC-13 S06 | 5 | DONE (PR #47) |
| 13 | Success Stories Page | EPIC-11 S06 | 5 | DONE (PR #52) |
| 14 | About & Educational Pages | EPIC-11 S03 | 8 | DONE (PR #36) |
| 15 | Multi-Language (ES + EN) | EPIC-11 S03 | 5 | DONE (PR #35) |

---

## Ticket ID Allocation

| Range | Version | Purpose |
|-------|---------|---------|
| RAP-001 to RAP-010 | Pre-V1 | Backend foundation (done) |
| RAP-011 to RAP-033 | V1 | MVP frontend + CI/CD (done) |
| RAP-034 to RAP-050 | V2 | Donations + EU compliance |
| RAP-051 to RAP-070 | V3 | Communications + workflow |
| RAP-071 to RAP-099 | V2/V3 | Remaining stories |
| RAP-100 to RAP-124 | V4 | Sprint 1: Staff Operations Launch |
| RAP-125 to RAP-149 | V5 | Sprint 2: Veterinary & Medical Records |
| RAP-150 to RAP-174 | V6 | Sprint 3: EU Payment Integration |
| RAP-175 to RAP-199 | V7 | Sprint 4: Volunteer & Foster Programs |
| RAP-200 to RAP-224 | V8 | Sprint 5: Notifications & Communications |
| RAP-225 to RAP-249 | V9 | Sprint 6: GDPR, Security & Compliance |
| RAP-250 to RAP-274 | V10 | Sprint 7: Analytics & Reporting |
| RAP-275 to RAP-299 | V11 | Sprint 8: Public Experience & Content |
| RAP-300 to RAP-324 | V12 | Sprint 9: Infrastructure & DevOps |
| RAP-325 to RAP-349 | V13 | Sprint 10: Mobile, Scale & Future |

---

## UX Sprint — EPIC-20: UX/UI Overhaul (38 points, 2 sprints)

**Audit:** `planning/epics/EPIC-20-ux-ui-overhaul/UX-AUDIT.md`
**Why now:** Site is live at sunstein.cloud/petShelter but speaks English to Paraguayan users, uses wrong brand colors, has 4 dead nav links, no WhatsApp. Must fix before driving traffic.

### Sprint UX-1: Foundation + Critical Fixes (23 pts)

| # | Story | Ticket | Pts | Status | Depends On |
|---|-------|--------|-----|--------|------------|
| 1 | Design System Realignment | RAP-171 | 5 | DONE (PR #33) | — |
| 2 | Spanish Translation & Warm Tone | RAP-172 | 5 | DONE (PR #35) | RAP-171 (color classes) |
| 3 | Missing Pages: About & Donate | RAP-173 | 5 | DONE (PR #36) | RAP-171, RAP-172 (strings) |
| 4 | Homepage Redesign with Trust Signals | RAP-175 | 5 | DONE (PR #38) | RAP-171, RAP-172 |
| 5 | WhatsApp + Accessibility (partial) | RAP-178 | 3 | DONE (PR #42) | RAP-172 (Spanish strings) |

### Sprint UX-2: Polish + Flow Optimization (15 pts)

| # | Story | Ticket | Pts | Status | Depends On |
|---|-------|--------|-----|--------|------------|
| 1 | Missing Pages: Volunteer & Foster | RAP-174 | 3 | DONE (PR #37) | RAP-171, RAP-172 |
| 2 | Animal Catalog UX Improvements | RAP-176 | 5 | DONE (PR #40) | RAP-171, RAP-172 |
| 3 | Animal Detail & Adoption Flow Overhaul | RAP-177 | 5 | DONE (PR #41) | RAP-171, RAP-172, RAP-176 |
| 4 | Accessibility Remainder (images, 404) | RAP-178 | 2 | DONE (PR #42) | RAP-171 |

---

## Rules

1. **Pick up top-to-bottom** — items are dependency-ordered
2. **One ticket at a time** — use `/start-ticket RAP-NNN`
3. **Run `make all-checks`** before every commit
4. **Update this file** when completing stories (move to Done)
5. **Never start a BLOCKED item** — check dependencies first
6. **Commit often** — small, focused commits with ticket IDs

---

## Future Sprints (V4-V13)

Full details in [ROADMAP.md](ROADMAP.md). Each sprint has epic and story docs in `planning/epics/EPIC-NN-*/` and sprint docs in `planning/sprints/sprint-NN/`.

| Sprint | Version | Theme | Points | Epics |
|--------|---------|-------|--------|-------|
| 1 | V4 | Staff Operations Launch | 105 | EPIC 21-25 |
| 2 | V5 | Veterinary & Medical Records | 105 | EPIC 26-30 |
| 3 | V6 | EU Payment Integration | 112 | EPIC 31-35 |
| 4 | V7 | Volunteer & Foster Programs | 99 | EPIC 36-40 |
| 5 | V8 | Notifications & Communications | 102 | EPIC 41-45 |
| 6 | V9 | GDPR, Security & Compliance | 87 | EPIC 46-50 |
| 7 | V10 | Analytics & Reporting | 101 | EPIC 51-55 |
| 8 | V11 | Public Experience & Content | 101 | EPIC 56-60 |
| 9 | V12 | Infrastructure & DevOps | 104 | EPIC 61-65 |
| 10 | V13 | Mobile, Scale & Future | 109 | EPIC 66-70 |

