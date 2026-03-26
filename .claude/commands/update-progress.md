# Command: /update-progress
**Usage**: `/update-progress` (uses active ticket from `tickets/current.md`)
**Aliases**: `/sync`, `/update-ticket`

---

## What This Does

Updates all ticket files to reflect the current state of work. Appends to progress.md, refreshes context.md, and adds timeline entries. Use this at session end, after milestones, or before switching tickets.

**Rules applied**: `.claude/rules/ticket-management.md`

---

## When to Use

- End of a working session
- After completing a significant milestone
- Before switching to a different ticket
- When context.md is stale (>1 session old)
- When asked to "sync" or "update the ticket"

---

## Workflow

### Step 1: Identify Active Ticket

```bash
cat tickets/current.md
```

Confirm ticket ID. If no active ticket: "No active ticket. Use /start-ticket RAP-NNN first."

### Step 2: Read Current State

Before updating, read:
```bash
cat tickets/$TICKET_ID/context.md
cat tickets/$TICKET_ID/progress.md
```

Understand:
- What was the previous state?
- What has changed since the last update?
- What decisions were made?

### Step 3: Update context.md

Replace the content with current state. This is a **live document** — update in place.

```markdown
# $TICKET_ID Context

## STATUS: ACTIVE
**Last updated**: [today's date and time]

## Current Focus
[What are we working on RIGHT NOW? Specific, not vague.]

## Technical State
[Key facts about the current state of the code/system:
 - What files have been modified
 - What patterns/approaches are being used
 - What works, what doesn't yet
 - Any important technical constraints discovered]

## Next Steps
1. [Immediate next action — specific]
2. [Following action]
3. [...]

## Blockers
[Any blocking issues, or: None]

## Key Decisions Made
- [Decision]: [why it was made] (add any new decisions from this session)
```

### Step 4: Append to progress.md

**APPEND ONLY** — never edit existing entries.

Add a new entry at the bottom:

```markdown
---
## [$TIMESTAMP] [Brief action description]
**Action**: [What was done in this session]
**Findings**: [What was discovered — technical insights, edge cases, surprises]
**Decision**: [Any decision made and the reasoning]
**Files changed**: [List of files modified/created]
**Next**: [What comes next]
```

Use multiple entries if this session had distinct phases:
```markdown
---
## [2026-03-25 14:30] Investigated root cause
**Action**: Read existing adoption form code
**Findings**: Validation is client-side only — no server-side validation exists
**Decision**: Will add both (API-level validation + form validation)
**Next**: Implement server-side validation endpoint

---
## [2026-03-25 15:45] Implemented server-side validation
**Action**: Added validateAdoptionRequest() to AdoptionService
**Files changed**: src/services/AdoptionService.py, tests/test_adoption.py
**Next**: Connect frontend form to use new validation endpoint
```

### Step 5: Append to timeline.md

Add session entry:

```markdown
| [YYYY-MM-DD HH:MM] | [Session/milestone description] | ~Xh |
```

### Step 6: Update references.md (if new files touched)

Append any new file references that are key to this ticket:

```markdown
## Key Files (updated)
- `src/services/AdoptionService.py` — main service, validateAdoptionRequest() added
- `tests/test_adoption.py` — unit tests for validation
- `src/api/adoption_routes.py` — API endpoint (to be modified next)
```

### Step 7: Confirm Update

```
✅ Ticket $TICKET_ID updated
   context.md: refreshed
   progress.md: 1 new entry added
   timeline.md: session entry added

   Status: ACTIVE
   Focus: [current focus]
   Next: [next step]
```

---

## Special Case: Session End

When ending a session, append to progress.md:

```markdown
---
## [$TIMESTAMP] Session End
**Action**: Wrapping up session
**Work done**: [Summary of what was accomplished this session]
**State**: [What's done, what's pending]
**Resume at**: [Exactly where to pick up next time]
```

---

## FINAL MUST-PASS CHECKLIST

- [ ] context.md reflects current accurate state
- [ ] progress.md has new entry appended (not edited)
- [ ] timeline.md has session timestamp
- [ ] No existing progress.md entries modified
- [ ] Blockers accurately documented (or marked None)
- [ ] Next steps are specific and actionable
