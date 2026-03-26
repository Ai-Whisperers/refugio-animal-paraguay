# Epic Analysis: Gaps, Improvements & Synergies

**Date**: 2026-03-26
**Purpose**: Cross-reference our 12 epics against industry standards, EU funder requirements, and Paraguay context to identify what's missing, what's weak, and what synergies we can exploit.

---

## Part 1: Issues in Current Epics

### Data Quality Issues

| Issue | Location | Fix |
|-------|----------|-----|
| EPIC-0 references Vitest/React Testing Library but backend is Python/FastAPI | EPIC-0, S01 | Rewrite for pytest/httpx — frontend testing is EPIC-11's concern |
| EPIC-0 references Supabase in MSW handlers but we use PostgreSQL + SQLAlchemy | EPIC-0, S02 | Remove Supabase references entirely |
| EPIC-1 references Prisma but we use SQLAlchemy/Alembic | EPIC-1, S01 | Fix ORM references |
| EPIC-1 references Cloudinary but we use local/S3 storage | EPIC-1, S04 | Fix storage references |
| EPIC-3 has "PayPal Integration" (S02) but roadmap decided on SEPA Direct Debit | EPIC-3, S02 | Replace PayPal with SEPA — PayPal fees too high for EU donors |
| EPIC-6 references Twilio but WhatsApp Cloud API is direct (no Twilio needed) | EPIC-6, S02 | Fix to Meta Cloud API |
| EPIC-8 mixes frontend (Playwright component) with backend (pytest) concerns | EPIC-8 | Split: backend testing vs frontend testing |
| EPIC-9 references Vercel/Heroku but we use Docker + VPS | EPIC-9, S03 | Fix hosting references |
| EPIC-10 has detailed story points but other epics don't | Mixed | Standardize estimation |
| EPIC-11 references Dutch language but primary locale is Spanish + English for EU | EPIC-11, S03 | Fix: Spanish primary, English for EU, Dutch optional |
| Acceptance criteria inconsistent — some say "All tasks completed" (meaningless), others have real criteria | EPIC-1,2,3,4,5 | Rewrite with testable Given/When/Then |

### Structural Issues

| Issue | Impact | Fix |
|-------|--------|-----|
| No Foster Program epic | V4 roadmap includes foster but no planning docs | Create EPIC-12: Foster Program |
| No Sponsorship/Campaign epic | Major revenue driver for EU donors, not planned | Add stories to EPIC-3 or create new epic |
| No Audit Logging epic or story | GDPR requires it, EU funders expect it | Add to EPIC-10 or create cross-cutting story |
| No Data Quality / Completeness checks | Incomplete animal records go unnoticed | Add story to EPIC-1 |
| No Post-Adoption Follow-up | Industry standard, critical for outcome reporting | Add stories to EPIC-2 |
| EPIC-7 has no funder-specific reporting | EU funders need impact reports, fund allocation | Add stories to EPIC-7 |
| No Onboarding / First-Run experience | Staff/volunteers need guided setup | Add to EPIC-10 or EPIC-11 |
| No Mobile optimization story | Paraguay is mobile-first (85%+ mobile web) | Add to EPIC-11 |
| No Animal Intake workflow | How animals enter the system is undefined | Add to EPIC-1 |

---

## Part 2: Missing Features (Not in Any Epic)

### Critical Gaps (Must Add)

#### 1. Animal Sponsorship System
**Why**: EU donors want tangible impact. "I sponsor Rocky's medical care" drives 3x higher retention than generic donations. Shelterluv and Pawlytics both offer this.

**Where it fits**: EPIC-3 (new stories) or new EPIC-13

**Stories needed**:
- Sponsorship tier creation (Bronze/Silver/Gold or per-animal)
- Sponsor-to-animal matching and tracking
- Sponsor update notifications (photo + progress)
- Sponsor dashboard (what my money funds)

#### 2. Post-Adoption Follow-up Protocol
**Why**: EU funders require outcome data. Return rates, satisfaction scores, and long-term welfare inform advocacy and funding applications.

**Where it fits**: EPIC-2 (new stories)

**Stories needed**:
- Automated follow-up schedule (7/30/90/365 days)
- Follow-up survey form (welfare check, satisfaction, photo request)
- Return/rehome tracking with reason codes
- Adoption outcome analytics

#### 3. Audit Trail / Activity Log
**Why**: GDPR Article 30 requires processing records. EU funders audit fund usage. Every sensitive action needs a trail.

**Where it fits**: Cross-cutting — new EPIC-13 or add to EPIC-10

**Stories needed**:
- Audit event capture (who, what, when, IP)
- Audit log viewer with filters (admin only)
- GDPR data processing log
- Automated retention and purge policy

#### 4. Animal Intake Workflow
**Why**: Currently no defined process for how animals enter the system. Intake condition, source, and initial assessment drive all downstream data.

**Where it fits**: EPIC-1 (new stories)

**Stories needed**:
- Intake form (source, condition, finder info, location found)
- Initial health assessment (linked to EPIC-4)
- Intake photos (before/after for impact reporting)
- Quarantine protocol trigger

#### 5. EU Funder Reporting Module
**Why**: Dutch owner has EU donor network. Funders expect quarterly/annual impact reports with fund allocation transparency. This is not just "CSV export" — it's structured impact storytelling.

**Where it fits**: EPIC-7 (new stories)

**Stories needed**:
- Impact report generator (PDF, quarterly/annual)
- Fund allocation tracking (% medical, food, operations, admin)
- Funder-specific dashboards (show Foundation X what their money did)
- Cost-per-animal and cost-per-adoption metrics

#### 6. In-Kind Donation Tracking
**Why**: Volunteers donate time, local businesses donate food/supplies, vets donate services. None of this is captured. EU funders value total support picture, not just cash.

**Where it fits**: EPIC-3 (new story)

**Stories needed**:
- In-kind donation recording (type, value, donor)
- In-kind donation reporting (total value contributed)

### High-Value Additions (Should Add)

#### 7. Behavioral Assessment Workflow
**Why**: Structured temperament assessments improve adoption matching and reduce returns. "Good with kids, needs experienced owner" is data, not just a text field.

**Where it fits**: EPIC-1 (new story) + EPIC-2 (matching logic)

#### 8. Lapsed Donor Re-engagement
**Why**: Highest ROI re-acquisition channel. Donor who gave once and stopped is 5x cheaper to re-engage than acquiring new donor.

**Where it fits**: EPIC-6 (new story) or EPIC-3

#### 9. Donation Campaign System
**Why**: Emergency vet fund, annual gala, specific rescue mission — campaigns with goals and progress bars drive urgency and social proof.

**Where it fits**: EPIC-3 (partially in EPIC-11 S04, needs backend)

#### 10. Volunteer Onboarding Checklist
**Why**: Structured onboarding with training verification reduces liability and improves retention.

**Where it fits**: EPIC-5 (new story)

#### 11. Capacity / Census Tracking
**Why**: "At current intake rate, shelter is full in 14 days" enables proactive fostering campaigns. Basic operational intelligence.

**Where it fits**: EPIC-7 (new story)

#### 12. PetFinder / Adopt-A-Pet Integration
**Why**: Syndicate adoptable animals to high-traffic listing sites. Free exposure to 10M+ monthly visitors.

**Where it fits**: EPIC-1 or EPIC-11 (new story)

---

## Part 3: Synergies Between Epics

### Synergy Map

```
EPIC-1 (Animals) ←→ EPIC-4 (Medical)
  Shared: animal_id, status transitions, timeline events
  Synergy: Medical hold status changes animal availability
  Action: Unified animal timeline component serves both

EPIC-2 (Adoption) ←→ EPIC-6 (Notifications)
  Shared: status change events
  Synergy: Every adoption state change triggers notification
  Action: Event bus pattern — adoption emits, notifications consume

EPIC-3 (Donations) ←→ EPIC-7 (Dashboard)
  Shared: donation data, aggregations
  Synergy: Dashboard needs real-time donation totals
  Action: Pre-computed materialized views serve both dashboard and reports

EPIC-3 (Donations) ←→ NEW: Sponsorship
  Shared: donor_id, payment processing
  Synergy: Sponsorship is a specialized recurring donation tied to an animal
  Action: Sponsorship extends donation model, not parallel to it

EPIC-5 (Volunteers) ←→ EPIC-6 (Notifications)
  Shared: user contact channels
  Synergy: Shift reminders, task assignments use notification engine
  Action: Build notification engine in V2 (email), extend in V3 (WhatsApp)

EPIC-1 (Animals) ←→ EPIC-2 (Adoption) ←→ NEW: Post-Adoption
  Shared: animal_id, adopter_id, outcome tracking
  Synergy: Intake → available → adopted → follow-up is ONE lifecycle
  Action: Animal timeline spans entire lifecycle, not just shelter stay

EPIC-10 (Auth) ←→ NEW: Audit Trail
  Shared: user identity, request context
  Synergy: Every authenticated action is an auditable event
  Action: Middleware captures audit events — build once, all epics benefit

EPIC-4 (Medical) ←→ EPIC-5 (Volunteers)
  Shared: task assignments (feeding, medication administration)
  Synergy: Medical care tasks assigned to trained volunteers
  Action: Task system tags tasks with required skill level

EPIC-7 (Dashboard) ←→ NEW: EU Funder Reporting
  Shared: aggregated metrics
  Synergy: Dashboard data feeds funder reports
  Action: Same query layer, different presentation (interactive vs PDF)

EPIC-11 (Public) ←→ EPIC-3 (Donations) ←→ NEW: Sponsorship
  Shared: public-facing donation/sponsorship experience
  Synergy: "Sponsor this animal" button on animal detail page
  Action: Design donation UX holistically — one-time, recurring, sponsorship
```

### Cross-Cutting Concerns (Build Once, Use Everywhere)

| Concern | Used By | Build In |
|---------|---------|----------|
| Event bus (emit/subscribe) | EPIC-2, 3, 4, 5, 6, 7 | V2 (in-process), V5 (Redis) |
| Notification dispatch | EPIC-2, 3, 4, 5, 6, 10 | V2 (email), V3 (WhatsApp) |
| Audit trail middleware | EPIC-2, 3, 4, 5, 7, 10 | V1 (foundation), expand per version |
| File/photo storage | EPIC-1, 4, 11 | V1 (local), V3 (S3/CDN) |
| PDF generation | EPIC-2, 3, 7 | V3 (contracts), V5 (reports) |
| Search infrastructure | EPIC-1, 5, 7, 11 | V5 (tsvector) |
| Multi-language | EPIC-6, 11 | V3 (foundation), V5 (complete) |
| Export (CSV/PDF) | EPIC-3, 5, 7 | V2 (CSV), V5 (PDF reports) |

---

## Part 4: Recommended New Epics

### EPIC-12: Foster Care Program

**Justification**: V4 roadmap already includes foster features but no planning epic exists. This is a distinct workflow with its own lifecycle.

**Stories**:
- S01: Foster Family Registration & Profiles
- S02: Foster Placement & Matching
- S03: Foster Check-in & Monitoring
- S04: Foster-to-Adopt Pathway
- S05: Foster Supply & Cost Tracking

### EPIC-13: Impact & Compliance

**Justification**: EU funder reporting, GDPR compliance, audit trail, and outcome tracking are scattered across epics but deserve dedicated ownership. This is what makes or breaks the EU funding relationship.

**Stories**:
- S01: Audit Trail System
- S02: GDPR Data Management (export, deletion, consent tracking)
- S03: Impact Report Generator
- S04: Fund Allocation Tracking
- S05: Outcome Metrics (post-adoption follow-up, return rates)

### EPIC-14: Sponsorship & Campaigns

**Justification**: Animal sponsorship and donation campaigns are the highest-impact revenue features for EU donor engagement. Currently buried in EPIC-3 S04 as "Donation Dashboard" which undersells it.

**Stories**:
- S01: Animal Sponsorship Tiers & Matching
- S02: Sponsor Update Notifications
- S03: Fundraising Campaign Creation & Management
- S04: Campaign Progress & Social Proof
- S05: In-Kind Donation Recording

---

## Part 5: Enhanced Stories for Existing Epics

### EPIC-1 Additions

| Story | Description | Version |
|-------|-------------|---------|
| S06: Animal Intake Workflow | Structured intake with source, condition, finder info, quarantine trigger | V1 |
| S07: Behavioral Assessment | Structured temperament evaluation form, compatibility scoring | V4 |
| S08: Data Completeness Alerts | Flag animals missing photos, vaccination records, or descriptions | V3 |
| S09: PetFinder/External Syndication | Auto-publish available animals to adoption listing sites | V5 |

### EPIC-2 Additions

| Story | Description | Version |
|-------|-------------|---------|
| S05: Post-Adoption Follow-up | Automated check-ins at 7/30/90/365 days, survey, photo request | V3 |
| S06: Adoption Matching Suggestions | Surface compatible animals based on adopter profile | V5 |
| S07: Adoption Fee Configuration | Per-species/age fee matrix, discount rules, waiver tracking | V2 |

### EPIC-3 Corrections & Additions

| Story | Change | Version |
|-------|--------|---------|
| S02: PayPal → SEPA Direct Debit | Replace PayPal with SEPA (EU donors, lower fees) | V2 |
| S05: Recurring Donation Management | Donor self-service: pause, resume, cancel, upgrade | V3 |
| S06: Cash Donation Recording | Staff logs walk-in cash/check donations | V2 |
| S07: Donation Channel Attribution | Track source: website, WhatsApp link, email, event | V3 |

### EPIC-5 Additions

| Story | Description | Version |
|-------|-------------|---------|
| S05: Volunteer Onboarding Checklist | Training modules, orientation signoff, safety briefing | V4 |
| S06: Volunteer Satisfaction Survey | Post-shift feedback, retention risk scoring | V5 |

### EPIC-7 Additions

| Story | Description | Version |
|-------|-------------|---------|
| S05: Capacity Census Dashboard | Current occupancy, intake/adoption rate, capacity forecast | V5 |
| S06: Funder-Specific Dashboards | Per-funder view: what their money funded, outcomes | V5 |

### EPIC-11 Additions

| Story | Description | Version |
|-------|-------------|---------|
| S05: Mobile-First Responsive Design | Paraguay is 85%+ mobile web — design for phones first | V1 |
| S06: Success Stories Gallery | Adopted animals with happy endings — drives donations | V3 |
| S07: SEO & Social Meta Tags | Structured data, OpenGraph, sitemap for discoverability | V3 |

---

## Part 6: Updated Totals

### Before Analysis

| Metric | Count |
|--------|-------|
| Epics | 12 |
| Stories | 46 |
| Tasks | ~122 |

### After Analysis

| Metric | Count | Delta |
|--------|-------|-------|
| Epics | 15 (+3 new) | +25% |
| Stories | 72 (+26 new) | +57% |
| Tasks | ~195 (estimated) | +60% |

### New Epic Summary

| Epic | Stories | Version | Priority |
|------|---------|---------|----------|
| EPIC-12: Foster Care Program | 5 | V4 | Medium |
| EPIC-13: Impact & Compliance | 5 | V2-V5 | High (EU funder critical) |
| EPIC-14: Sponsorship & Campaigns | 5 | V2-V3 | High (revenue driver) |

---

## Part 7: Priority Adjustments

Based on this analysis, the priority order shifts:

### Original Priority
1. EPIC-0 (Testing) / EPIC-10 (Auth) / EPIC-9 (Infra)
2. EPIC-1 (Animals) / EPIC-2 (Adoption)
3. EPIC-3 (Donations) / EPIC-6 (Notifications)
4. EPIC-4 (Medical) / EPIC-5 (Volunteers)
5. EPIC-7 (Dashboard) / EPIC-8 (QA) / EPIC-11 (Public)

### Recommended Priority (Revenue + Compliance First)
1. EPIC-10 (Auth) + EPIC-9 (Infra) + EPIC-11 (Public Portal) — **V1 foundations**
2. EPIC-3 (Donations) + **EPIC-13** (Impact/Compliance) + **EPIC-14** (Sponsorship) — **V2 revenue**
3. EPIC-6 (Notifications) + EPIC-2 (Adoption completion) — **V3 communication**
4. EPIC-4 (Medical) + EPIC-5 (Volunteers) + **EPIC-12** (Foster) — **V4 operations**
5. EPIC-7 (Dashboard) + EPIC-8 (QA) + EPIC-1 (search/syndication) — **V5 scale**

**Key shift**: EPIC-13 (Impact & Compliance) moves to V2 alongside donations. EU funders need to see accountability from day one of accepting money, not as a V5 afterthought.

---

*This analysis should be reviewed with the team and used to update individual epic files.*
