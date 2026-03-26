# Command: /complete-ticket
**Usage**: `/complete-ticket [TICKET-ID]`
**Example**: `/complete-ticket RAP-42`

If no ticket ID given, reads from `tickets/current.md`.

---

## What This Does

Runs comprehensive completion validation before closing a ticket. Creates recap and RCA documentation, makes the final commit, and cleans up active ticket state.

**This command enforces completion discipline** — it will STOP and report failures if validation doesn't pass. It will not close the ticket until all levels pass.

**Rules applied**: `.claude/rules/ticket-management.md`

---

## Workflow

### Step 0: STOP and Validate — Do Not Skip

When user says "done", "finished", "complete" about a ticket:
**STOP. Do not accept. Run all 4 validation levels first.**

This is not optional. This is the core discipline of the ticket system.

---

### Step 1: Identify Active Ticket

```bash
# Read from argument or current.md
cat tickets/current.md
```

Set `$TICKET_ID` to the active ticket.
Verify `tickets/$TICKET_ID/` exists. If not, error.

---

### Step 2: Level 1 Validation — File Completeness

Check all required files exist and have content:

```
- [ ] tickets/$TICKET_ID/plan.md — exists and has acceptance criteria
- [ ] tickets/$TICKET_ID/context.md — exists and is current
- [ ] tickets/$TICKET_ID/progress.md — exists with multiple entries
- [ ] tickets/$TICKET_ID/timeline.md — exists with session entries
```

If any fail: report specifically which files are missing/empty. STOP.

---

### Step 3: Level 2 Validation — Objective Fulfillment

Read `plan.md` and verify:

```
- [ ] All acceptance criteria checked off ([ ] → [x])
- [ ] No blockers listed in context.md
- [ ] No TODO/FIXME referencing this ticket in changed files
- [ ] context.md NEXT STEPS either empty or points to follow-up tickets
```

If any fail:
- List unchecked acceptance criteria explicitly
- List open blockers
- STOP. Do not proceed until user confirms or resolves.

---

### Step 4: Level 3 Validation — Production Readiness

Run quality checks:

```bash
# Run all quality gates (adapt to project's actual tools)
# Linting
ruff check .          # or: npm run lint

# Type checking
mypy src/             # or: npm run type-check

# Tests
pytest -q             # or: npm test

# Security
bandit -r src/ -ll    # or: npm audit
```

**Expected**: Zero errors, zero warnings, all tests passing.

Report results:
```
✅ Linting: clean
✅ Type check: clean
✅ Tests: 47 passing, 0 failing
✅ Security: clean
```

If any fail: List every error/warning. STOP. Do not proceed.

---

### Step 5: Level 4 Validation — Traceability

```
- [ ] All commits on this branch reference ticket ID ($TICKET_ID)
- [ ] timeline.md has reasonable session timestamps
- [ ] progress.md log covers all major work done
- [ ] No debug code left (console.log, print, breakpoints)
- [ ] No hardcoded test data or temporary values
```

Check git log:
```bash
git log --oneline develop.. | grep -v "^$TICKET_ID" | head -5
```

Report any commits without ticket ID reference.

---

### Step 6: Document Validation Evidence

Append to `tickets/$TICKET_ID/progress.md`:

```markdown
---
## [$TIMESTAMP] Completion Validation
**Action**: Ran all 4 validation levels before closure
**Level 1 (Files)**: ✅ All files present and complete
**Level 2 (Objectives)**: ✅ All X acceptance criteria satisfied
**Level 3 (Quality)**: ✅ Tests: X pass. Lint: clean. Types: clean.
**Level 4 (Traceability)**: ✅ All commits reference ticket ID
**Result**: READY TO CLOSE
```

---

### Step 7: Create recap.md

Create `tickets/$TICKET_ID/recap.md`:

```markdown
# $TICKET_ID Recap

## Outcome
[What was actually delivered — compare to objective in plan.md]

## Acceptance Criteria — Final Status
[Copy from plan.md with final status]
- [x] Criterion 1 — DONE
- [x] Criterion 2 — DONE

## Key Learnings
- [What would you do differently?]
- [What pattern was discovered?]
- [What took longer than expected and why?]

## Follow-Up Actions
- [ ] [Any follow-up tickets needed]
- [ ] [Monitoring to set up]
- [ ] [Documentation to update]

## Validation Evidence
- Tests: [N passing, 0 failing]
- Linting: clean
- Type check: clean
- Coverage: X%
```

---

### Step 8: Create rca.md (Defects Only)

If this was a bug/defect ticket, create `tickets/$TICKET_ID/rca.md`:

```markdown
# $TICKET_ID Root Cause Analysis

## Problem Statement
[What broke? What was the user impact?]

## Root Cause
**Why #1**: [Immediate symptom/cause]
**Why #2**: [Cause of why #1]
**Why #3**: [Root cause]

## Fix Applied
[What was changed to fix it]

## Prevention Strategies
- [ ] Test added: [description]
- [ ] Process improvement: [description]
- [ ] Documentation updated: [description]
```

---

### Step 9: Final Commit

```bash
git add tickets/$TICKET_ID/
git add [all changed source files]
git commit -m "$TICKET_ID: [summary of what was done] — ticket complete"
```

Commit message format: `RAP-42: Add adoption request form with validation — ticket complete`

---

### Step 10: Update State

Update `tickets/$TICKET_ID/context.md`:
```
## STATUS: COMPLETED
**Completed**: $TIMESTAMP
```

Clear `tickets/current.md` or remove it.

Add final entry to `tickets/$TICKET_ID/timeline.md`:
```
| $TIMESTAMP | Ticket closed | — |
```

---

### Step 11: Confirm Closure

Output:
```
✅ Ticket $TICKET_ID closed
   Validation: All 4 levels passed
   recap.md created
   Final commit: [$commit-sha] $TICKET_ID: ...
   tickets/current.md cleared

Next: Create PR feature/$TICKET_ID → develop
      Use /create-branch to verify branch state
```

---

## If Validation Fails

When any validation level fails:

1. State exactly what failed (specific file, criterion, test, warning)
2. Don't proceed to closure
3. Return control to user to resolve

```
❌ Ticket $TICKET_ID cannot be closed — validation failed:

Level 2 — Objectives:
  • Acceptance criterion not met: "Adoption form shows validation errors inline"
    (currently shows a generic alert dialog — see plan.md line 12)

Level 3 — Quality:
  • 2 linting warnings in src/components/AdoptionForm.tsx:
    - Line 47: no-unused-vars (requestId)
    - Line 89: prefer-const (formData)
  • Test failure: AdoptionForm.test.tsx:34 — "submit button disabled until required fields filled"

Fix these issues and run /complete-ticket again.
```

---

## FINAL MUST-PASS CHECKLIST

- [ ] All 4 validation levels passed and documented in progress.md
- [ ] recap.md created with outcomes and learnings
- [ ] rca.md created if defect ticket
- [ ] Final commit references ticket ID, message includes "ticket complete"
- [ ] context.md STATUS set to COMPLETED
- [ ] tickets/current.md cleared
- [ ] No uncommitted changes related to this ticket
