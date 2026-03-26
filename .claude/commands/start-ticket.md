# Command: /start-ticket
**Usage**: `/start-ticket [TICKET-ID] [brief description]`
**Example**: `/start-ticket RAP-42 adoption request form`

---

## What This Does

Initializes a ticket with full documentation structure. Creates all required files, performs complexity assessment, and sets this as the active ticket.

**Rules applied**: `.claude/rules/ticket-management.md`

---

## Workflow

### Step 1: Validate Input

Confirm:
- Ticket ID format is `RAP-NNN` (or alternative project prefix)
- Description is clear enough to write an objective

If ticket ID is missing, ask: "What's the ticket ID? (format: RAP-NNN)"
If no description, ask: "What does this ticket achieve in one sentence?"

### Step 2: Check for Existing Work

```bash
# Check if ticket folder already exists
ls tickets/$TICKET_ID/ 2>/dev/null
```

If exists: read `context.md` and ask "This ticket already has work. Resume it?"
If resuming: update STATUS to ACTIVE, append to progress.md, stop here.

### Step 3: Create Ticket Structure

```bash
mkdir -p tickets/$TICKET_ID
```

### Step 4: Create plan.md

Create `tickets/$TICKET_ID/plan.md` following the template in `ticket-management.md`:

```markdown
# $TICKET_ID Plan

## Objective
[One sentence — what does this ticket achieve?]

## Description
[2-4 sentences of context. Why does this need to exist?]

## Acceptance Criteria
- [ ] [Criterion 1 — testable, specific]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Complexity Assessment
**Track**: [Simple Fix / Complex Implementation]

### Simple Fix Criteria (ALL must be met)
- [ ] Single, clear root cause identified
- [ ] Solution affects ≤3 files
- [ ] Change impact ≤10 lines of actual code
- [ ] Low risk of side effects
- [ ] Solution pattern is well-understood

**Assessment**: [Simple Fix / Complex] — [1-2 sentence justification]

## Approach
[High-level implementation strategy.
 For Complex: phases.
 For Simple: direct approach.]

## Dependencies
- Depends on: None (or list)

## Risks
- [Risk: description] → Mitigation: [plan]
```

**Ask the user** (if not enough info to fill in):
- "What are the acceptance criteria? (what must be true when this is done?)"
- "Any dependencies or blockers I should know about?"

### Step 5: Create context.md

Create `tickets/$TICKET_ID/context.md`:

```markdown
# $TICKET_ID Context

## STATUS: ACTIVE
**Last updated**: [today's date]

## Current Focus
Initial analysis and implementation planning.

## Technical State
[Empty — to be filled as work progresses]

## Next Steps
1. Review acceptance criteria and confirm scope
2. Identify files to modify
3. Begin implementation

## Blockers
None

## Key Decisions Made
None yet
```

### Step 6: Create progress.md

Create `tickets/$TICKET_ID/progress.md`:

```markdown
# $TICKET_ID Progress Log

---
## [$TIMESTAMP] Session Start — Ticket Initialized
**Action**: Created ticket structure and plan
**Complexity track**: [Simple Fix / Complex]
**Next**: [First action based on plan]
```

### Step 7: Create timeline.md

Create `tickets/$TICKET_ID/timeline.md`:

```markdown
# $TICKET_ID Timeline

| Timestamp | Event | Duration |
|-----------|-------|---------|
| $TIMESTAMP | Ticket initialized | — |
```

### Step 8: Create references.md

Create `tickets/$TICKET_ID/references.md`:

```markdown
# $TICKET_ID References

## Key Files
[To be filled as work progresses]

## Related Tickets
[Any related work]

## External Resources
[Docs, APIs, specs relevant to this ticket]
```

### Step 9: Update current.md

Update or create `tickets/current.md`:

```markdown
# Active Ticket

**Ticket**: $TICKET_ID
**Since**: $TIMESTAMP
**Description**: $DESCRIPTION
```

### Step 10: Confirm and Begin

Output summary:
```
✅ Ticket $TICKET_ID initialized
   Track: [Simple Fix / Complex]
   Files created: plan.md, context.md, progress.md, timeline.md, references.md
   Active: tickets/current.md updated

Ready to begin. First step: [first action from plan]
```

---

## Complexity Assessment Decision Tree

```
Evaluate ALL Simple Fix criteria:
  1. Single, clear root cause identified?
  2. ≤3 files affected?
  3. ≤10 lines of actual code changed?
  4. Low risk of side effects?
  5. Solution pattern is well-understood?

ALL yes → Simple Fix Track
ANY no  → Complex Implementation Track
Unsure  → Complex (better to over-plan)
```

---

## FINAL MUST-PASS CHECKLIST

- [ ] plan.md created with objective, acceptance criteria, complexity assessment
- [ ] context.md created with STATUS: ACTIVE
- [ ] progress.md created with initialization entry
- [ ] timeline.md created with first timestamp
- [ ] references.md created
- [ ] tickets/current.md updated with this ticket
- [ ] Complexity track documented and justified
