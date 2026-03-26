# Development Queue — Refugio Animal Paraguay

**Last updated**: 2026-03-26
**Active version**: V1 (MVP)
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
| 4 | SEPA Direct Debit | EPIC-3 S02 | 8 | PR #27 (conflicts) |
| 5 | GDPR Consent Tracking | EPIC-13 S07 | 5 | DONE (PR #26) |
| 6 | Cash Donation Recording | EPIC-3 S06 | 3 | DONE (PR #16) |
| 7 | In-Kind Donation Recording | EPIC-14 S05 | 5 | DONE (PR #17) |
| 8 | Sponsorship Tiers & Matching | EPIC-14 S01 | 8 | PR #28 (conflicts) |
| 9 | Campaign Management | EPIC-14 S03 | 6 | PR #29 (conflicts) |
| 10 | Donation Landing Page | EPIC-11 S04 | 13 | READY |
| 11 | Donation Dashboard (Staff) | EPIC-3 S04 | 6 | BLOCKED on #4 |
| 12 | Email Notification System | EPIC-6 S01 | 8 | DONE (PR #18) |
| 13 | GDPR Data Export | EPIC-13 S02 | 6 | PR #30 (conflicts) |

---

## V3 — Communications (Weeks 9-12)

| # | Story | Epic | Points | Status |
|---|-------|------|--------|--------|
| 1 | WhatsApp Integration | EPIC-6 S02 | 8 | |
| 2 | In-App Notifications | EPIC-6 S03 | 6 | DONE (PR #32) |
| 3 | Notification Preferences | EPIC-6 S04 | 5 | PR #34 (conflicts) |
| 4 | Adoption Notifications (status changes) | EPIC-2 S03 | 5 | DONE (PR #39) |
| 5 | PDF Adoption Contracts | EPIC-2 S04 | 6 | PR #43 (conflicts) |
| 6 | Post-Adoption Follow-up | EPIC-2 S05 | 8 | PR #44 (conflicts) |
| 7 | Tigo Money Integration (PYG) | EPIC-3 S03 | 8 | |
| 8 | Sponsor Update Notifications | EPIC-14 S02 | 6 | |
| 9 | Campaign Progress & Social Proof | EPIC-14 S04 | 5 | |
| 10 | Impact Report Generator | EPIC-13 S03 | 7 | |
| 11 | Fund Allocation Tracking | EPIC-13 S04 | 6 | DONE (PR #45) |
| 12 | GDPR Data Deletion | EPIC-13 S06 | 5 | PR #31 (conflicts) |
| 13 | Success Stories Page | EPIC-11 S06 | 5 | |
| 14 | About & Educational Pages | EPIC-11 S03 | 8 | |
| 15 | Multi-Language (ES + EN) | EPIC-11 S03 | 5 | |

---

## V4 — Operations (Weeks 13-18)

| # | Story | Epic | Points |
|---|-------|------|--------|
| 1 | Medical Record Schema & API | EPIC-4 S01 | 8 |
| 2 | Veterinary Notes & Documents | EPIC-4 S02 | 6 |
| 3 | Medical Timeline & History | EPIC-4 S03 | 5 |
| 4 | Vaccination & Medication Tracking | EPIC-4 S04 | 8 |
| 5 | Volunteer Registration & Profiles | EPIC-5 S01 | 5 |
| 6 | Volunteer Onboarding Checklist | EPIC-5 S05 | 5 |
| 7 | Shift Scheduling System | EPIC-5 S02 | 8 |
| 8 | Task Assignment & Tracking | EPIC-5 S03 | 6 |
| 9 | Volunteer Recognition & Analytics | EPIC-5 S04 | 5 |
| 10 | Foster Family Registration | EPIC-12 S01 | 5 |
| 11 | Foster Placement & Matching | EPIC-12 S02 | 8 |
| 12 | Foster Check-in & Monitoring | EPIC-12 S03 | 6 |
| 13 | Foster-to-Adopt Pathway | EPIC-12 S04 | 6 |
| 14 | Foster Supply & Cost Tracking | EPIC-12 S05 | 5 |
| 15 | Outcome Metrics & Analytics | EPIC-13 S05 | 7 |

---

## V5 — Analytics & Scale (Weeks 19-24)

| # | Story | Epic | Points |
|---|-------|------|--------|
| 1 | Admin Dashboard & Analytics | EPIC-7 S01 | 8 |
| 2 | User & Role Management UI | EPIC-7 S02 | 6 |
| 3 | Content & Settings Management | EPIC-7 S03 | 5 |
| 4 | Reporting & Export | EPIC-7 S04 | 6 |
| 5 | Admin Panel Localization | EPIC-7 S05 | 5 |
| 6 | Advanced Search & Filters (tsvector) | EPIC-1 S05 | 8 |
| 7 | Password Reset + Email Verification | EPIC-10 S02 (complete) | 5 |
| 8 | Profile Management | EPIC-10 S03 | 5 |
| 9 | E2E Testing (Playwright) | EPIC-8 S03 | 8 |
| 10 | Performance & Security Testing | EPIC-8 S04 | 6 |
| 11 | Production Deployment & TLS | EPIC-9 S03 | 8 |
| 12 | Monitoring & Logging | EPIC-9 S04 | 6 |

---

## V6 — Reporting & Multi-Shelter (Weeks 25-32)

| # | Story | Epic | Points |
|---|-------|------|--------|
| 1 | Financial Reporting Dashboard | EPIC-15 S01 | 8 |
| 2 | EU Tax Compliance Exports | EPIC-15 S02 | 7 |
| 3 | Donor Retention & Impact Reports | EPIC-15 S03 | 6 |
| 4 | Operational KPI Dashboard | EPIC-15 S04 | 7 |
| 5 | Multi-Shelter Location Management | EPIC-16 S01 | 8 |
| 6 | Inter-Shelter Animal Transfers | EPIC-16 S02 | 8 |
| 7 | Location-Specific Staff & Permissions | EPIC-16 S03 | 6 |
| 8 | Consolidated Cross-Shelter Reporting | EPIC-16 S04 | 7 |

---

## V7 — Community, Mobile & API Platform (Weeks 33-42)

| # | Story | Epic | Points |
|---|-------|------|--------|
| 1 | Success Stories Publishing | EPIC-17 S01 | 5 |
| 2 | Social Media Integration | EPIC-17 S02 | 6 |
| 3 | Adopter Community Forum | EPIC-17 S03 | 8 |
| 4 | Community Events Management | EPIC-17 S04 | 5 |
| 5 | Mobile App — Staff Field Operations | EPIC-18 S01 | 13 |
| 6 | Mobile App — Volunteer Shift & Tasks | EPIC-18 S02 | 8 |
| 7 | Mobile App — Push Notifications | EPIC-18 S03 | 5 |
| 8 | Public REST API & Developer Docs | EPIC-19 S01 | 8 |
| 9 | Government Animal Registration Integration | EPIC-19 S02 | 8 |
| 10 | Webhook System for Partners | EPIC-19 S03 | 6 |
| 11 | Tigo Money Payment Integration | EPIC-19 S04 | 8 |

---

## Ticket ID Allocation

| Range | Version | Purpose |
|-------|---------|---------|
| RAP-001 to RAP-010 | Pre-V1 | Backend foundation (done) |
| RAP-011 to RAP-033 | V1 | MVP frontend + CI/CD (done) |
| RAP-034 to RAP-050 | V2 | Donations + EU compliance |
| RAP-051 to RAP-070 | V3 | Communications + workflow |
| RAP-071 to RAP-095 | V4 | Operations |
| RAP-096 to RAP-120 | V5 | Analytics + scale |
| RAP-121 to RAP-140 | V6 | Reporting + multi-shelter |
| RAP-141 to RAP-170 | V7 | Community + mobile + API platform |
| RAP-171 to RAP-178 | UX | UX/UI overhaul (EPIC-20) |

---

## UX Sprint — EPIC-20: UX/UI Overhaul (38 points, 2 sprints)

**Audit:** `planning/epics/EPIC-20-ux-ui-overhaul/UX-AUDIT.md`
**Why now:** Site is live at sunstein.cloud/petShelter but speaks English to Paraguayan users, uses wrong brand colors, has 4 dead nav links, no WhatsApp. Must fix before driving traffic.

### Sprint UX-1: Foundation + Critical Fixes (23 pts)

| # | Story | Ticket | Pts | Status | Depends On |
|---|-------|--------|-----|--------|------------|
| 1 | Design System Realignment | RAP-171 | 5 | DONE (PR #33) | — |
| 2 | Spanish Translation & Warm Tone | RAP-172 | 5 | READY | RAP-171 (color classes) |
| 3 | Missing Pages: About & Donate | RAP-173 | 5 | READY | RAP-171, RAP-172 (strings) |
| 4 | Homepage Redesign with Trust Signals | RAP-175 | 5 | READY | RAP-171, RAP-172 |
| 5 | WhatsApp + Accessibility (partial) | RAP-178 | 3 | READY | RAP-172 (Spanish strings) |

### Sprint UX-2: Polish + Flow Optimization (15 pts)

| # | Story | Ticket | Pts | Status | Depends On |
|---|-------|--------|-----|--------|------------|
| 1 | Missing Pages: Volunteer & Foster | RAP-174 | 3 | READY | RAP-171, RAP-172 |
| 2 | Animal Catalog UX Improvements | RAP-176 | 5 | READY | RAP-171, RAP-172 |
| 3 | Animal Detail & Adoption Flow Overhaul | RAP-177 | 5 | READY | RAP-171, RAP-172, RAP-176 |
| 4 | Accessibility Remainder (images, 404) | RAP-178 | 2 | READY | RAP-171 |

---

## Rules

1. **Pick up top-to-bottom** — items are dependency-ordered
2. **One ticket at a time** — use `/start-ticket RAP-NNN`
3. **Run `make all-checks`** before every commit
4. **Update this file** when completing stories (move to Done)
5. **Never start a BLOCKED item** — check dependencies first
6. **Commit often** — small, focused commits with ticket IDs
