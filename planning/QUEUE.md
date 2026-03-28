# Development Queue — Refugio Animal Paraguay

**Last updated**: 2026-03-28
**Active version**: V6 Sprint 3 EPIC-33 COMPLETE | New epics EPIC-76 to EPIC-93 queued
**Full roadmap**: [ROADMAP.md](ROADMAP.md) — 16 sprints, 68 epics, ~395 stories
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
| 9 | Campaign Management | EPIC-14 S03 | 6 | DONE (PR #55) |
| 10 | Donation Landing Page | EPIC-11 S04 | 13 | DONE (PR #51) |
| 11 | Donation Dashboard (Staff) | EPIC-3 S04 | 6 | DONE (PR #56) |
| 12 | Email Notification System | EPIC-6 S01 | 8 | DONE (PR #18) |
| 13 | GDPR Data Export | EPIC-13 S02 | 6 | DONE (PR #48) |

---

## V3 — Communications (Weeks 9-12)

| # | Story | Epic | Points | Status |
|---|-------|------|--------|--------|
| 1 | WhatsApp Integration | EPIC-6 S02 | 8 | DONE (PR #57) |
| 2 | In-App Notifications | EPIC-6 S03 | 6 | DONE (PR #32) |
| 3 | Notification Preferences | EPIC-6 S04 | 5 | DONE (PR #34) |
| 4 | Adoption Notifications (status changes) | EPIC-2 S03 | 5 | DONE (PR #39) |
| 5 | PDF Adoption Contracts | EPIC-2 S04 | 6 | DONE (PR #43) |
| 6 | Post-Adoption Follow-up | EPIC-2 S05 | 8 | DONE (PR #44) |
| 7 | Tigo Money Integration (PYG) | EPIC-3 S03 | 8 | DONE (PR #58) |
| 8 | Sponsor Update Notifications | EPIC-14 S02 | 6 | DONE (PR #59) |
| 9 | Campaign Progress & Social Proof | EPIC-14 S04 | 5 | DONE (PR #60) |
| 10 | Impact Report Generator | EPIC-13 S03 | 7 | DONE (PR #50) |
| 11 | Fund Allocation Tracking | EPIC-13 S04 | 6 | DONE (PR #45) |
| 12 | GDPR Data Deletion | EPIC-13 S06 | 5 | DONE (PR #47) |
| 13 | Success Stories Page | EPIC-11 S06 | 5 | DONE (PR #52) |
| 14 | About & Educational Pages | EPIC-11 S03 | 8 | DONE (PR #36) |
| 15 | Multi-Language (ES + EN) | EPIC-11 S03 | 5 | DONE (PR #35) |

---

## V4 Sprint 1 — Staff Operations Launch (EPIC-21, 18 pts) — COMPLETE

| # | Story | Ticket | Pts | Status |
|---|-------|--------|-----|--------|
| 1 | Staff Login Page with JWT Auth | RAP-100 | 5 | DONE (PR #61) |
| 2 | Password Reset with Email Token | RAP-101 | 3 | DONE (PR #62) |
| 3 | Email Verification on Registration | RAP-102 | 3 | DONE |
| 4 | Session Timeout & Forced Logout | RAP-103 | 3 | DONE |
| 5 | Account Lockout After Failed Attempts | RAP-104 | 4 | DONE |

---

## V4 Sprint 1.5 — EPIC-23: Adoption Request Queue (21 pts) — COMPLETE

| # | Story | Ticket | Pts | Status |
|---|-------|--------|-----|--------|
| 1 | Adoption request list page with status filters | RAP-110 | 5 | DONE (PR #97) |
| 2 | Application detail view with adopter info | RAP-111 | 3 | DONE (PR #98) |
| 3 | Approve/reject workflow with mandatory notes | RAP-112 | 5 | DONE (PR #99) |
| 4 | Automated email on status change (bilingual) | RAP-113 | 5 | DONE (PR #100) |
| 5 | Adoption request analytics (time to decision) | RAP-114 | 3 | DONE (PR #101) |

---

## V6 Sprint 3 — EU Payment Integration: EPIC-31 SEPA (25 pts) — COMPLETE

| # | Story | Ticket | Pts | Status |
|---|-------|--------|-----|--------|
| 1 | SEPA SetupIntent endpoint + saved payment methods list | RAP-150 | 5 | DONE (PR #138) |
| 2 | SEPA mandate creation flow (Next.js multi-step frontend) | RAP-151 | 8 | DONE (PR #139) |
| 3 | SEPA webhook handling (processing, mandate, setup events) | RAP-152 | 5 | DONE (PR #140) |
| 4 | SEPA payment status tracking endpoint | RAP-153 | 4 | DONE (PR #141) |
| 5 | SEPA-specific donor notifications service | RAP-154 | 3 | DONE (PR #142) |

---

## EPIC-32: Recurring Donations (26 pts) — COMPLETE

**Goal**: Monthly giving program — Stripe subscriptions, donor management, cancellation, and upgrade flows.

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Subscription model and Stripe integration | RAP-155 | 8 | DONE (PR #143) | Backend |
| 2 | Monthly giving signup flow | RAP-156 | 5 | DONE (PR #144) | Frontend |
| 3 | Subscription management (pause, cancel, upgrade) | RAP-157 | 5 | DONE (PR #145) | Fullstack |
| 4 | Recurring donation dashboard for donors | RAP-158 | 3 | DONE (PR #146) | Frontend |
| 5 | Failed payment retry and dunning emails | RAP-159 | 5 | DONE (PR #147) | Backend |

---

## EPIC-33: Sponsorship & Campaign System (23 pts)

**Goal**: Animal sponsorship tiers, fundraising campaigns with goals, progress tracking, and social proof.

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Sponsorship tier model and API | RAP-160 | 5 | DONE (pre-existing, EPIC-14 S01 PR #54) | Backend |
| 2 | Campaign creation and management | RAP-161 | 5 | DONE (PR #148) | Fullstack |
| 3 | Campaign progress tracking and widgets | RAP-162 | 5 | DONE (PR #149) | Frontend |
| 4 | Sponsor dashboard with animal updates | RAP-163 | 5 | DONE (PR #150) | Frontend |
| 5 | Social proof widgets (recent donors, progress bars) | RAP-164 | 3 | DONE (PR #151) | Frontend |

---

## V3.1 — Priority Sprint: Stability & Quality Gates (92 pts, 25 stories)

**Why now**: CI/CD deploys to production with ZERO tests. 14 bare `except Exception` blocks. Frontend has P0 bugs (/animals 404, no Stripe.js, no error boundaries). No structured logging, no monitoring, no staging environment. These must be fixed before adding more features.

**Execute order**: P0 stories first (top-to-bottom within each priority tier). All P0 stories MUST complete before any P1 starts.

### P0 — Critical (must fix immediately)

| # | Story | Ticket | Epic | Pts | Status | Depends On |
|---|-------|--------|------|-----|--------|------------|
| 1 | Add test + lint pipeline to GitHub Actions | RAP-400 | EPIC-71 | 5 | DONE (PR #66) | — |
| 2 | Add security scanning (bandit + pip-audit) | RAP-401 | EPIC-71 | 3 | DONE (PR #67) | RAP-400 |
| 3 | Password reset tests (0% → 80%) | RAP-405 | EPIC-72 | 5 | DONE (PR #91) | RAP-101 (PR #62 merged) |
| 4 | Adoption requests coverage (41% → 80%) | RAP-406 | EPIC-72 | 3 | DONE (PR #69) | — |
| 5 | Replace bare except Exception handlers | RAP-410 | EPIC-73 | 3 | DONE (PR #70) | — |
| 6 | Structured JSON logging (structlog) | RAP-415 | EPIC-74 | 5 | DONE (PR #74) | — |
| 7 | Sentry error tracking integration | RAP-416 | EPIC-74 | 3 | DONE (PR #75) | RAP-415 |
| 8 | Add error.tsx and loading.tsx boundaries | RAP-420 | EPIC-75 | 3 | DONE (PR #76) | — |
| 9 | Fix /animals page 404 rendering bug | RAP-421 | EPIC-75 | 3 | DONE (PR #77) | — |
| 10 | Integrate Stripe.js Elements into DonationForm | RAP-422 | EPIC-75 | 5 | DONE (PR #89) | — |

### P1 — High Priority (after all P0 complete)

| # | Story | Ticket | Epic | Pts | Status | Depends On |
|---|-------|--------|------|-----|--------|------------|
| 11 | Create staging environment with approval gate | RAP-402 | EPIC-71 | 5 | DONE (PR #90) | RAP-400 ✓ |
| 12 | Harden Docker production image | RAP-403 | EPIC-71 | 3 | DONE (PR #68) | — |
| 13 | Notification handler exception tests | RAP-407 | EPIC-72 | 3 | DONE (PR #71) | — |
| 14 | Audit middleware tests | RAP-408 | EPIC-72 | 3 | DONE (PR #72) | — |
| 15 | Audit API input validation gaps | RAP-411 | EPIC-73 | 3 | DONE (PR #73) | — |
| 16 | Standardize error responses across routers | RAP-412 | EPIC-73 | 5 | DONE (PR #79) | RAP-410 |
| 17 | Database constraint error handling | RAP-413 | EPIC-73 | 3 | DONE (PR #80) | RAP-412 |
| 18 | Payment error handling (Stripe + Tigo) | RAP-414 | EPIC-73 | 3 | DONE (PR #81) | RAP-412 |
| 19 | Health check improvements | RAP-417 | EPIC-74 | 3 | DONE (PR #82) | — |
| 20 | Request/response logging middleware | RAP-418 | EPIC-74 | 3 | DONE (PR #83) | RAP-415 |
| 21 | Database backup automation | RAP-419 | EPIC-74 | 5 | DONE (PR #84) | — |
| 22 | Loading and error states on all pages | RAP-423 | EPIC-75 | 5 | DONE (PR #86) | RAP-420 |
| 23 | Centralized API error handling (frontend) | RAP-424 | EPIC-75 | 3 | DONE (PR #85) | RAP-420 |

### P2 — Medium Priority (after all P1 complete)

| # | Story | Ticket | Epic | Pts | Status | Depends On |
|---|-------|--------|------|-----|--------|------------|
| 24 | Coverage reporting and PR status checks | RAP-404 | EPIC-71 | 5 | DONE (PR #88) | RAP-400 ✓ |
| 25 | Frontend component tests (Vitest) | RAP-409 | EPIC-72 | 3 | DONE (PR #87) | — |

### Epics in this sprint

| Epic | Theme | Stories | Points |
|------|-------|---------|--------|
| EPIC-71 | CI/CD Quality Gates | RAP-400 to RAP-404 | 21 |
| EPIC-72 | Test Coverage Gaps | RAP-405 to RAP-409 | 18 |
| EPIC-73 | Exception Handling & Validation | RAP-410 to RAP-414 | 16 |
| EPIC-74 | Logging & Observability | RAP-415 to RAP-419 | 19 |
| EPIC-75 | Frontend Stability | RAP-420 to RAP-424 | 18 |

---

## Ticket ID Allocation

| Range | Version | Purpose |
|-------|---------|---------|
| RAP-001 to RAP-010 | Pre-V1 | Backend foundation (done) |
| RAP-011 to RAP-033 | V1 | MVP frontend + CI/CD (done) |
| RAP-034 to RAP-050 | V2 | Donations + EU compliance |
| RAP-051 to RAP-070 | V3 | Communications + workflow |
| RAP-071 to RAP-099 | V2/V3 | Remaining stories |
| RAP-100 to RAP-124 | V4 | Sprint 1: Staff Operations Launch (done) |
| RAP-125 to RAP-149 | V5 | Sprint 2: Veterinary & Medical Records |
| RAP-150 to RAP-174 | V6 | Sprint 3: EU Payment Integration |
| RAP-175 to RAP-199 | V7 | Sprint 4: Volunteer & Foster Programs |
| RAP-200 to RAP-224 | V8 | Sprint 5: Notifications & Communications |
| RAP-225 to RAP-249 | V9 | Sprint 6: GDPR, Security & Compliance |
| RAP-250 to RAP-274 | V10 | Sprint 7: Analytics & Reporting |
| RAP-275 to RAP-299 | V11 | Sprint 8: Public Experience & Content |
| RAP-300 to RAP-324 | V12 | Sprint 9: Infrastructure & DevOps |
| RAP-325 to RAP-349 | V13 | Sprint 10: Mobile, Scale & Future |
| RAP-400 to RAP-424 | V3.1 | Priority Sprint: Stability & Quality Gates (done) |
| RAP-500 to RAP-506 | V14 | Sprint 11: EPIC-76 Public Registration |
| RAP-507 to RAP-516 | V14 | Sprint 11: EPIC-77 Vet Vouchers |
| RAP-517 to RAP-524 | V14 | Sprint 11: EPIC-78 Adoption Pre-Qualification |
| RAP-525 to RAP-532 | V14 | Sprint 12: EPIC-79 Castration Campaigns |
| RAP-533 to RAP-542 | V14 | Sprint 13: EPIC-80 Rescuer Network |
| RAP-543 to RAP-550 | V14 | Sprint 12: EPIC-81 Flexible Donations |
| RAP-551 to RAP-558 | V14 | Sprint 13: EPIC-82 Content Management |
| RAP-559 to RAP-565 | V14 | Sprint 12: EPIC-83 Photo Upload |
| RAP-566 to RAP-572 | V14 | Sprint 13: EPIC-84 Social Sharing |
| RAP-573 to RAP-579 | V14 | Sprint 12: EPIC-85 Real-Time Dashboard |
| RAP-580 to RAP-587 | V14 | Sprint 14: EPIC-86 Emergency Cases |
| RAP-588 to RAP-595 | V14 | Sprint 14: EPIC-87 Adoption Workflow |
| RAP-596 to RAP-603 | V14 | Sprint 14: EPIC-88 Mobile PWA |
| RAP-604 to RAP-611 | V14 | Sprint 14: EPIC-89 Financial Transparency |
| RAP-612 to RAP-617 | V15 | Sprint 15: EPIC-90 Community Survey |
| RAP-618 to RAP-624 | V15 | Sprint 15: EPIC-91 Transport Logistics |
| RAP-625 to RAP-631 | V15 | Sprint 15: EPIC-92 Education Hub |
| RAP-632 to RAP-639 | V16 | Sprint 16: EPIC-93 Analytics Platform |

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

## Sprint 11 — Public Engagement Foundation (123 pts, 3 epics)

**Goal**: Public registration, vet vouchers, adoption pre-qualification — the features stakeholders requested most urgently.

### EPIC-76: Public User Registration & Unified Portal (35 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Self-registration form | RAP-500 | 5 | DONE (PR #152) | Fullstack |
| 2 | Email verification flow with token | RAP-501 | 3 | DONE (PR #153) | Backend |
| 3 | Unified personal dashboard | RAP-502 | 8 | DONE (PR #154) | Fullstack |
| 4 | Profile management page | RAP-503 | 5 | DONE (PR #155) | Fullstack |
| 5 | Social login (Google OAuth) | RAP-504 | 5 | DONE (PR #159) | Fullstack |
| 6 | WhatsApp-based phone verification | RAP-505 | 5 | DONE (PR #156) | Backend |
| 7 | Role self-assignment | RAP-506 | 4 | DONE (PR #157) | Fullstack |

### EPIC-77: Veterinary Voucher & Direct Clinic Donation (50 pts)

| # | Story | Ticket | Pts | Status | Track | Depends On |
|---|-------|--------|-----|--------|-------|------------|
| 1 | Partner veterinary clinic registration model and API | RAP-507 | 5 | DONE (PR #158) | Backend | — |
| 2 | Clinic service catalog with pricing | RAP-508 | 5 | DONE (PR #160) | Backend | RAP-507 |
| 3 | Voucher purchase flow for donors | RAP-509 | 8 | DONE (PR #164) | Fullstack | RAP-508 |
| 4 | VetVoucher model and lifecycle API | RAP-510 | 5 | DONE (PR #161) | Backend | RAP-507 |
| 5 | Rescuer voucher wallet and claim flow | RAP-511 | 5 | DONE (PR #166) | Fullstack | RAP-510, RAP-500 |
| 6 | Clinic redemption interface | RAP-512 | 5 | DONE (PR #163) | Fullstack | RAP-510 |
| 7 | Donor transparency notifications | RAP-513 | 3 | DONE (PR #165) | Backend | RAP-509 |
| 8 | Voucher expiry and refund policy | RAP-514 | 3 | DONE (PR #162) | Backend | RAP-510 |
| 9 | Financial reconciliation dashboard | RAP-515 | 5 | DONE (PR #207) | Fullstack | RAP-512 |
| 10 | Public voucher statistics dashboard | RAP-516 | 3 | DONE (PR #208) | Fullstack | RAP-515 |

### EPIC-78: Adoption Pre-Qualification & Smart Matching (38 pts)

| # | Story | Ticket | Pts | Status | Track | Depends On |
|---|-------|--------|-----|--------|-------|------------|
| 1 | Configurable adoption requirements model | RAP-517 | 5 | DONE (PR #167) | Backend | — |
| 2 | Pre-qualification questionnaire API | RAP-518 | 5 | DONE (PR #168) | Backend | RAP-517 |
| 3 | Pre-qualification form UI | RAP-519 | 8 | DONE (PR #209) | Frontend | RAP-518 |
| 4 | Qualification result page with alternatives | RAP-520 | 5 | DONE (PR #211) | Frontend | RAP-519 |
| 5 | Admin requirement configuration UI | RAP-521 | 5 | DONE (PR #210) | Frontend | RAP-517 |
| 6 | Smart matching algorithm | RAP-522 | 5 | DONE (PR #173) | Backend | RAP-518 |
| 7 | Pre-qualification analytics | RAP-523 | 3 | DONE (PR #174) | Backend | RAP-518 |
| 8 | Anti-gaming protection | RAP-524 | 2 | DONE (PR #175) | Backend | RAP-518 |

---

## Sprint 12 — Campaigns & Donations (143 pts, 4 epics)

**Goal**: Castration campaigns, flexible donations, photo management, real-time dashboards.

### EPIC-79: Castration Campaign Engine (38 pts)

| # | Story | Ticket | Pts | Status | Track | Depends On |
|---|-------|--------|-----|--------|-------|------------|
| 1 | Castration campaign model and creation API | RAP-525 | 5 | DONE (in develop) | Backend | — |
| 2 | Public castration campaign page with live counter | RAP-526 | 8 | DONE (PR #212) | Fullstack | RAP-525 |
| 3 | Integration with vet voucher system | RAP-527 | 5 | DONE (PR #170) | Backend | RAP-510 (EPIC-77) |
| 4 | Photo gallery for completed castrations | RAP-528 | 5 | DONE (PR #213) | Fullstack | RAP-525 |
| 5 | Donor leaderboard | RAP-529 | 3 | DONE (PR #214) | Fullstack | RAP-526 |
| 6 | Castration drive scheduling | RAP-530 | 5 | DONE (PR #216) | Fullstack | RAP-525 |
| 7 | Post-campaign impact report | RAP-531 | 5 | DONE (PR #217) | Fullstack | RAP-525 |
| 8 | Social media sharing with auto-generated cards | RAP-532 | 2 | DONE (PR #215) | Frontend | RAP-526 |

### EPIC-81: Flexible Donation Targets (40 pts)

| # | Story | Ticket | Pts | Status | Track | Depends On |
|---|-------|--------|-----|--------|-------|------------|
| 1 | Donation target type system | RAP-543 | 5 | DONE (PR #171) | Backend | — |
| 2 | Animal sponsorship page | RAP-544 | 5 | READY | Fullstack | RAP-543 |
| 3 | Rescuer support page | RAP-545 | 5 | READY | Fullstack | RAP-543, RAP-533 (EPIC-80) |
| 4 | Clinic fund page | RAP-546 | 5 | READY | Fullstack | RAP-543, RAP-507 (EPIC-77) |
| 5 | Need-specific donation | RAP-547 | 3 | READY | Fullstack | RAP-543 |
| 6 | Donation allocation tracking API | RAP-548 | 5 | DONE (PR #172) | Backend | RAP-543 |
| 7 | Impact notification system | RAP-549 | 5 | DONE (PR #176) | Backend | RAP-548 |
| 8 | Fund management dashboard | RAP-550 | 5 | READY | Fullstack | RAP-548 |

### EPIC-83: Photo Upload & Media Management (35 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Image upload endpoint with validation | RAP-559 | 5 | DONE (PR #178) | Backend |
| 2 | Image optimization pipeline | RAP-560 | 5 | DONE (PR #179) | Backend |
| 3 | Storage backend (local + S3 compatible) | RAP-561 | 5 | DONE (PR #180) | Backend |
| 4 | Animal photo gallery management UI | RAP-562 | 5 | IN_REVIEW (PR #230) | Frontend |
| 5 | Medical document upload with validation | RAP-563 | 3 | DONE (PR #181) | Backend |
| 6 | Campaign and story image uploads | RAP-564 | 3 | IN_REVIEW (PR #231) | Fullstack |
| 7 | Image CDN headers | RAP-565 | 3 | DONE (PR #182) | Backend |

### EPIC-85: Real-Time Dashboard & Live Statistics (30 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Public statistics API | RAP-573 | 3 | DONE (PR #177) | Backend |
| 2 | Homepage live statistics | RAP-574 | 3 | DONE (PR #218) | Frontend |
| 3 | Public impact page | RAP-575 | 5 | IN_REVIEW (PR #227) | Fullstack |
| 4 | Castration counter widget | RAP-576 | 3 | DONE (PR #219) | Fullstack |
| 5 | Admin real-time activity feed | RAP-577 | 5 | IN_REVIEW (PR #229) | Fullstack |
| 6 | Real-time donation notifications | RAP-578 | 5 | DONE (PR #183) | Backend |
| 7 | Campaign real-time progress | RAP-579 | 3 | DONE (PR #225) | Frontend |

---

## Sprint 13 — Community & Content (155 pts, 3 epics)

**Goal**: Rescuer network, content management, social sharing — community building features.

### EPIC-80: Community Rescuer Network (55 pts)

| # | Story | Ticket | Pts | Status | Track | Depends On |
|---|-------|--------|-----|--------|-------|------------|
| 1 | Rescuer self-registration and profile model | RAP-533 | 5 | DONE (PR #184) | Backend | RAP-500 (EPIC-76) |
| 2 | Rescuer profile page | RAP-534 | 8 | READY | Fullstack | RAP-533 |
| 3 | Rescuer animal listing management | RAP-535 | 8 | READY | Fullstack | RAP-533 |
| 4 | Rescuer campaign creation | RAP-536 | 5 | READY | Fullstack | RAP-534 |
| 5 | Needs board | RAP-537 | 5 | READY | Fullstack | RAP-533 |
| 6 | Community feed | RAP-538 | 5 | READY | Fullstack | RAP-534 |
| 7 | Donor choice interface | RAP-539 | 5 | READY | Fullstack | RAP-543 (EPIC-81) |
| 8 | Rescuer verification system | RAP-540 | 3 | DONE (PR #185) | Backend | RAP-533 |
| 9 | Admin moderation tools | RAP-541 | 5 | READY | Fullstack | RAP-533 |
| 10 | Integration with vet voucher system | RAP-542 | 3 | DONE (PR #186) | Backend | RAP-510 (EPIC-77) |

### EPIC-82: Content Management System (40 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | CMS content model and API | RAP-551 | 5 | DONE (PR #187) | Backend |
| 2 | Homepage dynamic content | RAP-552 | 5 | READY | Fullstack |
| 3 | Admin content editor | RAP-553 | 8 | READY | Frontend |
| 4 | Success stories CRUD | RAP-554 | 5 | READY | Fullstack |
| 5 | News/blog posts | RAP-555 | 5 | READY | Fullstack |
| 6 | Featured animals on homepage | RAP-556 | 3 | READY | Fullstack |
| 7 | Featured campaigns on homepage | RAP-557 | 3 | READY | Fullstack |
| 8 | Multilingual content support | RAP-558 | 5 | DONE (PR #188) | Backend |

### EPIC-84: Social Sharing & WhatsApp Deep Integration (30 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Open Graph meta tags for all public pages | RAP-566 | 5 | READY | Frontend |
| 2 | WhatsApp share buttons on animal cards | RAP-567 | 3 | IN_REVIEW (PR #226) | Frontend |
| 3 | WhatsApp share for campaigns | RAP-568 | 3 | IN_REVIEW (PR #228) | Frontend |
| 4 | Social media share buttons (Facebook, Instagram, Twitter) | RAP-569 | 3 | READY | Frontend |
| 5 | Share tracking analytics | RAP-570 | 5 | DONE (PR #189) | Backend |
| 6 | Referral tracking | RAP-571 | 5 | DONE (on develop) | Backend |
| 7 | Auto-generated social media cards | RAP-572 | 3 | DONE | Backend |

---

## Sprint 14 — Operations & Mobile (154 pts, 4 epics)

**Goal**: Emergency cases, advanced adoption workflow, PWA, financial transparency.

### EPIC-86: Emergency & Urgent Case System (35 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Emergency case model and creation API | RAP-580 | 5 | DONE | Backend |
| 2 | Emergency case creation form | RAP-581 | 5 | READY | Fullstack |
| 3 | Emergency featured on homepage | RAP-582 | 5 | READY | Frontend |
| 4 | Push notifications to donors | RAP-583 | 3 | DONE | Backend |
| 5 | Simplified 1-click donation for emergencies | RAP-584 | 5 | READY | Fullstack |
| 6 | Auto-close when funded | RAP-585 | 3 | DONE | Backend |
| 7 | Post-emergency update | RAP-586 | 3 | READY | Fullstack |
| 8 | Emergency analytics | RAP-587 | 3 | DONE | Backend |

### EPIC-87: Advanced Adoption Workflow (40 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Configurable adoption pipeline stages | RAP-588 | 5 | DONE | Backend |
| 2 | Pipeline status tracking API | RAP-589 | 5 | DONE | Backend |
| 3 | Adoption pipeline board UI | RAP-590 | 8 | READY | Frontend |
| 4 | Home visit scheduling | RAP-591 | 5 | READY | Fullstack |
| 5 | Trial period management | RAP-592 | 5 | READY | Fullstack |
| 6 | Post-adoption follow-up automation | RAP-593 | 5 | DONE | Backend |
| 7 | Return/exchange management | RAP-594 | 3 | DONE | Backend |
| 8 | Adoption success scoring | RAP-595 | 5 | DONE | Backend |

### EPIC-88: Mobile-First PWA (41 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | PWA manifest and service worker setup | RAP-596 | 5 | READY | Frontend |
| 2 | Responsive design audit and fixes | RAP-597 | 6 | READY | Frontend |
| 3 | Camera integration for forms | RAP-598 | 7 | READY | Fullstack |
| 4 | Offline donation forms with IndexedDB | RAP-599 | 6 | READY | Fullstack |
| 5 | Web push notifications | RAP-600 | 6 | READY | Fullstack |
| 6 | Touch-friendly admin interface | RAP-601 | 4 | READY | Frontend |
| 7 | App-like bottom navigation bar | RAP-602 | 4 | READY | Frontend |
| 8 | Performance optimization and bundling | RAP-603 | 3 | READY | Fullstack |

### EPIC-89: Financial Transparency & Impact Reporting (38 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Expense recording system | RAP-604 | 6 | READY | Fullstack |
| 2 | Expense management UI with receipts | RAP-605 | 5 | READY | Frontend |
| 3 | Financial transparency dashboard | RAP-606 | 7 | READY | Fullstack |
| 4 | Campaign-specific financial reports | RAP-607 | 5 | READY | Fullstack |
| 5 | Donor impact summaries | RAP-608 | 6 | READY | Fullstack |
| 6 | Automated monthly impact emails | RAP-609 | 4 | DONE (PR #206) | Backend |
| 7 | Annual financial report generation | RAP-610 | 3 | READY | Backend |
| 8 | Expense approval workflow | RAP-611 | 2 | READY | Fullstack |

---

## Sprint 15 — Community Engagement (86 pts, 3 epics)

**Goal**: Surveys, transport logistics, education hub — deepening community involvement.

### EPIC-90: Community Survey & Feedback System (26 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Survey model with question types | RAP-612 | 5 | DONE | Backend |
| 2 | Admin survey creation form | RAP-613 | 6 | READY | Fullstack |
| 3 | Public survey response collection | RAP-614 | 4 | READY | Fullstack |
| 4 | Survey results analytics dashboard | RAP-615 | 5 | READY | Fullstack |
| 5 | Community feature request board | RAP-616 | 3 | READY | Frontend |
| 6 | Survey distribution via WhatsApp/email | RAP-617 | 3 | PR #205 | Backend |

### EPIC-91: Animal Transport & Logistics Network (29 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Transport request model and API | RAP-618 | 4 | DONE | Backend |
| 2 | Transport request creation form | RAP-619 | 5 | READY | Fullstack |
| 3 | Volunteer driver registration | RAP-620 | 5 | READY | Fullstack |
| 4 | Intelligent request matching and notification | RAP-621 | 6 | READY | Fullstack |
| 5 | Real-time trip tracking with photos | RAP-622 | 4 | READY | Fullstack |
| 6 | Integration with vet appointments | RAP-623 | 3 | PR #204 | Backend |
| 7 | Driver reimbursement tracking | RAP-624 | 2 | PR #203 | Backend |

### EPIC-92: Education & Responsible Pet Ownership Hub (31 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Educational article model and API | RAP-625 | 4 | PR #202 | Backend |
| 2 | Education hub public page | RAP-626 | 5 | READY | Frontend |
| 3 | Article detail page with related articles | RAP-627 | 5 | READY | Frontend |
| 4 | Required pre-adoption reading enforcement | RAP-628 | 4 | READY | Fullstack |
| 5 | Sterilization awareness campaign page | RAP-629 | 4 | READY | Frontend |
| 6 | Video embed support | RAP-630 | 3 | READY | Frontend |
| 7 | Admin article editor with rich text | RAP-631 | 6 | READY | Fullstack |

---

## Sprint 16 — Analytics & Intelligence (41 pts, 1 epic)

**Goal**: Comprehensive reporting and analytics platform across all domains.

### EPIC-93: Reporting & Analytics Dashboard (41 pts)

| # | Story | Ticket | Pts | Status | Track |
|---|-------|--------|-----|--------|-------|
| 1 | Executive KPI dashboard | RAP-632 | 7 | READY | Fullstack |
| 2 | Animal intake/outcome analytics | RAP-633 | 6 | READY | Fullstack |
| 3 | Donation analytics and trends | RAP-634 | 5 | READY | Fullstack |
| 4 | Donor analytics and retention | RAP-635 | 5 | READY | Fullstack |
| 5 | Veterinary care analytics | RAP-636 | 4 | READY | Fullstack |
| 6 | Community engagement analytics | RAP-637 | 5 | READY | Fullstack |
| 7 | Exportable reports (PDF/CSV) | RAP-638 | 4 | READY | Fullstack |
| 8 | Predictive analytics and forecasting | RAP-639 | 5 | READY | Backend |

---

## Future Sprints (V4 Sprint 2 through V13 + V14-V16)

Full details in [ROADMAP.md](ROADMAP.md). Each sprint has epic and story docs in `planning/epics/EPIC-NN-*/` and sprint docs in `planning/sprints/sprint-NN/`.

**V4 Sprint 1 (EPIC-21) is COMPLETE.** V3.1 Priority Sprint is COMPLETE. EPIC-32 S5 is next.

| Sprint | Version | Theme | Points | Epics |
|--------|---------|-------|--------|-------|
| — | V3.1 | ~~Priority: Stability & Quality Gates~~ | ~~92~~ | ~~EPIC 71-75~~ DONE |
| 1 | V4 | Staff Operations Launch (S1 done, S2+ pending) | 105 | EPIC 21-25 |
| 2 | V5 | Veterinary & Medical Records | 105 | EPIC 26-30 |
| 3 | V6 | EU Payment Integration | 112 | EPIC 31-35 |
| 4 | V7 | Volunteer & Foster Programs | 99 | EPIC 36-40 |
| 5 | V8 | Notifications & Communications | 102 | EPIC 41-45 |
| 6 | V9 | GDPR, Security & Compliance | 87 | EPIC 46-50 |
| 7 | V10 | Analytics & Reporting | 101 | EPIC 51-55 |
| 8 | V11 | Public Experience & Content | 101 | EPIC 56-60 |
| 9 | V12 | Infrastructure & DevOps | 104 | EPIC 61-65 |
| 10 | V13 | Mobile, Scale & Future | 109 | EPIC 66-70 |
| 11 | V14 | **Public Engagement Foundation** | **123** | **EPIC 76-78** |
| 12 | V14 | **Campaigns & Donations** | **143** | **EPIC 79, 81, 83, 85** |
| 13 | V14 | **Community & Content** | **125** | **EPIC 80, 82, 84** |
| 14 | V14 | **Operations & Mobile** | **154** | **EPIC 86-89** |
| 15 | V15 | **Community Engagement** | **86** | **EPIC 90-92** |
| 16 | V16 | **Analytics & Intelligence** | **41** | **EPIC 93** |

