# Agent Work Guide — Refugio Animal Paraguay

This guide explains how autonomous agents find, claim, and implement stories from the roadmap.

## Quick Start

1. Read `QUEUE.md` — check for READY stories in V2/V3 (highest priority)
2. If no V2/V3 READY stories, read `ROADMAP.md` — find next planned story by sprint order
3. Read the story's `STORY.md` for acceptance criteria
4. Create branch from develop: `feature/RAP-NNN-brief-description`
5. Implement, test, commit often with ticket ID
6. Create PR targeting develop
7. Update story status on develop (not in feature branch)

---

## Project Structure

```
planning/
├── QUEUE.md                  ← Active queue (V1-V3 stories with live status)
├── ROADMAP.md                ← 10-sprint roadmap index (V4-V13, 50 epics)
├── AGENT-GUIDE.md            ← This file
├── CLAIMING.md               ← Legacy claiming log
├── orchestrator-log.md       ← Automated checker run history
├── sprints/
│   ├── sprint-01/SPRINT.md   ← Sprint 1 goal, epics, deliverables
│   ├── sprint-02/SPRINT.md
│   └── ...sprint-10/
├── epics/
│   ├── EPIC-1-animal-catalog-and-management/    ← V1 epics (1-20)
│   │   ├── EPIC.md
│   │   └── stories/S01-*/STORY.md
│   ├── EPIC-21-staff-login-auth-hardening/      ← V4+ epics (21-70)
│   │   ├── EPIC.md
│   │   └── stories/S1-*/STORY.md
│   └── ...
```

## Story Discovery (Priority Order)

### Priority 1: V2/V3 READY stories in QUEUE.md
These are partially completed versions. Finish them first.

```
Read planning/QUEUE.md
Find first READY story in V2 or V3
```

### Priority 2: V4+ stories from ROADMAP.md (Sprint Order)
After V2/V3 are complete, work the 10-sprint roadmap in order.

```
Sprint 1 (V4): EPIC-21 through EPIC-25 — Staff Operations Launch
Sprint 2 (V5): EPIC-26 through EPIC-30 — Veterinary & Medical Records
Sprint 3 (V6): EPIC-31 through EPIC-35 — EU Payment Integration
Sprint 4 (V7): EPIC-36 through EPIC-40 — Volunteer & Foster Programs
Sprint 5 (V8): EPIC-41 through EPIC-45 — Notifications & Communications
Sprint 6 (V9): EPIC-46 through EPIC-50 — GDPR, Security & Compliance
Sprint 7 (V10): EPIC-51 through EPIC-55 — Analytics & Reporting
Sprint 8 (V11): EPIC-56 through EPIC-60 — Public Experience & Content
Sprint 9 (V12): EPIC-61 through EPIC-65 — Infrastructure & DevOps
Sprint 10 (V13): EPIC-66 through EPIC-70 — Mobile, Scale & Future
```

Within each sprint: work epics in order (EPIC-21 before EPIC-22). Within each epic: work S1 before S2. P0 stories before P1.

### Reading a Story
```
planning/epics/EPIC-NN-slug/stories/SN-slug/STORY.md
```
The STORY.md frontmatter contains: ticket ID, points, priority, track, sprint, status.
The body contains: acceptance criteria (Given/When/Then), definition of done, technical notes.

---

## Implementation Workflow

### 1. Create Ticket and Branch
- Use the ticket ID from STORY.md frontmatter (e.g., RAP-100)
- Create ticket directory: `tickets/RAP-NNN/` with plan.md, context.md, progress.md, timeline.md
- Branch from develop: `feature/RAP-NNN-brief-description`

### 2. Implement
- Read relevant source files before modifying
- Backend: Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2 (in `src/`)
- Frontend: Next.js 14, Tailwind CSS, TypeScript (in `frontend/`)
- Write tests: `tests/unit/test_*.py` and `tests/integration/test_*.py`
- Commit often: `RAP-NNN: Add X` (imperative mood)

### 3. Quality Gates
```bash
PYTHONPATH=. python3 -m ruff check .
PYTHONPATH=. python3 -m black --check .
PYTHONPATH=. python3 -m pytest tests/ --tb=short -q
```

### 4. Create PR
```bash
unset GITHUB_TOKEN && gh auth switch --user IvanWeissVanDerPol
git push -u origin feature/RAP-NNN-brief-description
gh pr create --base develop --title "RAP-NNN: Brief description" --body "..."
```

### 5. Update Status (on develop, NOT in feature branch)
```bash
git checkout develop
# For V2/V3: edit QUEUE.md status to DONE (PR #XX)
# For V4+: edit STORY.md frontmatter status to "done"
git commit -m "Housekeeping: Mark RAP-NNN as DONE (PR #XX)"
git push origin develop
```

---

## GitHub Auth Fix
Before ANY git push or gh command:
```bash
unset GITHUB_TOKEN && gh auth switch --user IvanWeissVanDerPol
```

## Conflict Prevention

### Rule 1: Never update QUEUE.md in a feature branch
Update it on develop directly after creating the PR. This prevents merge conflict cascades.

### Rule 2: One story per agent per run
Don't try to do multiple stories in a single session.

### Rule 3: Lock file coordination
Worker creates `/tmp/refugio-worker.lock` while running. Checker skips PR merges when lock exists.

### Rule 4: PRs always target develop
Never target another feature branch. Never target main directly.

---

## Ticket ID Allocation

| Range | Version | Sprint |
|-------|---------|--------|
| RAP-001 to RAP-010 | Pre-V1 | Foundation (done) |
| RAP-011 to RAP-033 | V1 | MVP (done) |
| RAP-034 to RAP-070 | V2/V3 | Donations + Communications |
| RAP-100 to RAP-124 | V4 | Sprint 1: Staff Operations |
| RAP-125 to RAP-149 | V5 | Sprint 2: Veterinary |
| RAP-150 to RAP-174 | V6 | Sprint 3: EU Payments |
| RAP-175 to RAP-199 | V7 | Sprint 4: Volunteer/Foster |
| RAP-200 to RAP-224 | V8 | Sprint 5: Notifications |
| RAP-225 to RAP-249 | V9 | Sprint 6: GDPR/Security |
| RAP-250 to RAP-274 | V10 | Sprint 7: Analytics |
| RAP-275 to RAP-299 | V11 | Sprint 8: Public Experience |
| RAP-300 to RAP-324 | V12 | Sprint 9: Infrastructure |
| RAP-325 to RAP-349 | V13 | Sprint 10: Mobile/Scale |

---

## Rollback Procedures

### Broken Feature Branch
```bash
git branch -D feature/RAP-NNN-description
git push origin --delete feature/RAP-NNN-description
```

### Broken PR
```bash
gh pr close <PR-NUMBER>
```

### Database Migration Rollback
```bash
PYTHONPATH=. python3 -m alembic history
PYTHONPATH=. python3 -m alembic downgrade -1
```

---

**Last updated**: 2026-03-26
**Roadmap**: 10 sprints, 50 epics, 250 stories, ~1,010 story points
