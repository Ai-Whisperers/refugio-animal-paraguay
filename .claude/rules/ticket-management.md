# Rule: Ticket Management
**ID**: rule.ticket.management.v1
**Version**: 1.0.0
**Applies to**: All work tracked in `tickets/` folder

---

## Ticket File Structure

```
tickets/
├── current.md              ← Active ticket ID (local only, not committed)
├── templates/
│   ├── plan-template.md
│   ├── context-template.md
│   ├── progress-template.md
│   └── recap-template.md
└── RAP-123/
    ├── plan.md
    ├── context.md
    ├── progress.md
    ├── timeline.md
    ├── references.md
    ├── recap.md            ← Created at closure
    └── rca.md              ← Created for defects
```

---

## plan.md Structure

```markdown
# RAP-123 Plan

## Objective
One clear sentence stating what this ticket achieves.

## Description
2-4 sentences of context. Why does this need to exist?

## Acceptance Criteria
- [ ] Criterion 1 (testable, specific)
- [ ] Criterion 2
- [ ] Criterion 3

## Complexity Assessment
**Track**: Simple Fix | Complex Implementation

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified
- [ ] Solution affects ≤3 files
- [ ] Change impact ≤10 lines of actual code
- [ ] Low risk of side effects
- [ ] Solution pattern is well-understood

**Assessment result**: [Simple Fix / Complex] — [justification]

## Approach
High-level implementation strategy. For Complex tickets: phases.

## Dependencies
- Depends on: [other tickets/PRs]
- Blocked by: [blockers]

## Risks
- Risk: [description] → Mitigation: [plan]
```

---

## context.md Structure

```markdown
# RAP-123 Context

## STATUS: ACTIVE | PAUSED | COMPLETED
**Last updated**: YYYY-MM-DD HH:MM

## Current Focus
What are we working on RIGHT NOW?

## Technical State
Key technical facts: files touched, decisions made, patterns used.

## Next Steps
1. Immediate next action
2. Following action
3. ...

## Blockers
- [Blocker description] → [Status/resolution]

## Key Decisions Made
- Decision 1: [why]
- Decision 2: [why]

## RESUME POINT (if PAUSED)
Exactly where to resume: [clear description]
```

---

## progress.md Structure

**APPEND ONLY** — Never edit existing entries. Add new entries at the bottom.

```markdown
# RAP-123 Progress Log

---
## [YYYY-MM-DD HH:MM] Session Start
**Action**: Started ticket work
**Findings**: [Initial analysis]
**Next**: [What comes next]

---
## [YYYY-MM-DD HH:MM] [Action taken]
**Action**: [What was done]
**Findings**: [What was discovered]
**Decision**: [Any decision made and why]
**Next**: [What comes next]
```

---

## timeline.md Structure

```markdown
# RAP-123 Timeline

| Timestamp | Event | Duration |
|-----------|-------|---------|
| YYYY-MM-DD HH:MM | Session start | — |
| YYYY-MM-DD HH:MM | [Milestone] | ~Xh |
| YYYY-MM-DD HH:MM | Session end | — |

## Session Summary
- Total sessions: N
- Estimated hours: X
```

---

## recap.md Structure (at closure)

```markdown
# RAP-123 Recap

## Outcome
What was actually delivered? (vs what was planned)

## Acceptance Criteria — Final Status
- [x] Criterion 1 — DONE
- [x] Criterion 2 — DONE
- [ ] Criterion 3 — DEFERRED to RAP-456

## Key Learnings
- Learning 1
- Learning 2

## Follow-Up Actions
- [ ] RAP-456: [description]
- [ ] [Monitoring needed]

## Validation Evidence
- Tests: [X passing, 0 failing]
- Linting: clean
- Type check: clean
- Coverage: X%
```

---

## rca.md Structure (defects only)

```markdown
# RAP-123 Root Cause Analysis

## Problem Statement
What broke, and what was the user impact?

## Root Cause
The actual cause, not the symptom. Go 5 levels deep if needed.

**Why #1**: [Immediate cause]
**Why #2**: [Cause of cause 1]
**Why #3**: [...]

## Contributing Factors
- Factor 1
- Factor 2

## Timeline
When was the defect introduced? When was it detected?

## Fix Applied
What was changed to fix it?

## Prevention Strategies
How do we prevent this class of bug in the future?
- [ ] Add test: [description]
- [ ] Update process: [description]
```

---

## Lifecycle Workflow

### Phase 1: Initialization

1. Create `tickets/RAP-123/` directory
2. Create `plan.md` — objective, acceptance criteria
3. Run complexity assessment — document in plan.md
4. Create `context.md` — STATUS: ACTIVE
5. Create `progress.md` — first entry: ticket started
6. Create `timeline.md` — first timestamp
7. Update `tickets/current.md` — set active ticket

### Phase 2: Active Work

- Update `context.md` each session (STATUS, focus, next steps)
- Append to `progress.md` for significant actions/decisions
- Append to `timeline.md` for session start/end
- Update `references.md` as files are touched

### Phase 3: Completion Claim

When user says "done", "finished", or "complete":

**STOP. Do not accept yet. Run validation:**

**Level 1 — File completeness**:
- [ ] plan.md exists and has acceptance criteria
- [ ] context.md exists and is current
- [ ] progress.md exists with entries
- [ ] timeline.md has session timestamps

**Level 2 — Objective fulfillment**:
- [ ] All acceptance criteria in plan.md are checked off
- [ ] No open blockers in context.md
- [ ] Nothing marked TODO or FIXME for this ticket

**Level 3 — Production readiness**:
- [ ] Zero linting errors/warnings
- [ ] Zero type errors
- [ ] All tests pass
- [ ] No skipped tests without justification
- [ ] No hardcoded credentials or secrets

**Level 4 — Traceability**:
- [ ] All commits reference ticket ID (RAP-123: ...)
- [ ] timeline.md has session end timestamp

Document validation evidence in progress.md. Only proceed to closure after all levels pass.

### Phase 4: Closure

1. Create `recap.md`
2. Create `rca.md` if this was a defect ticket
3. Final commit: `RAP-123: [summary] — ticket complete`
4. Update `context.md` STATUS: COMPLETED
5. Clear `tickets/current.md`

---

## Switching Discipline

When switching from one ticket to another:

1. **Pause current ticket**:
   - Update `context.md`: STATUS: PAUSED, RESUME_POINT: [clear description]
   - Append to `progress.md`: "Paused — switching to RAP-456"
   - Commit in-progress work

2. **Update** `tickets/current.md` to new ticket ID

3. **Resume target ticket**:
   - Read `context.md` RESUME_POINT
   - Append to `progress.md`: "Resumed from RAP-123"
   - Continue work

**Never switch without logging** — breaks the audit trail.

---

## Implementation Tracks

### Simple Fix Track
All criteria met: single cause, ≤3 files, ≤10 lines, low risk, known pattern.
- Lightweight plan.md
- Direct implementation
- Still requires Level 1-4 validation before closing

### Complex Implementation Track
Any criterion failed.
- Comprehensive plan.md with phases
- Progress tracked per phase
- Context.md updated frequently
- Full validation required

---

## FINAL MUST-PASS CHECKLIST

Before claiming ticket work complete:
- [ ] Completion discipline applied — all 4 validation levels run
- [ ] Validation evidence documented in progress.md
- [ ] recap.md created with outcome and learnings
- [ ] rca.md created if defect ticket
- [ ] All commits reference ticket ID
- [ ] context.md STATUS set to COMPLETED
- [ ] tickets/current.md cleared
- [ ] OPSEC clean — no credentials, personal data, server names
