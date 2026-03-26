# Command: /switch-ticket
**Usage**: `/switch-ticket [TARGET-TICKET-ID]`
**Example**: `/switch-ticket RAP-56`

---

## What This Does

Safely switches from the current active ticket to a different one. Saves all current state, logs the switch in both tickets, and resumes the target ticket.

**Core principle**: Never switch context without logging. Maintain the audit trail.

**Rules applied**: `.claude/rules/ticket-management.md`

---

## Workflow

### Step 1: Identify Current Ticket

```bash
cat tickets/current.md
```

Set `$CURRENT_ID` to the active ticket.
Set `$TARGET_ID` to the argument provided.

If same ticket: "Already working on $TARGET_ID."
If no active ticket: Skip to Step 4 (just start target ticket).

### Step 2: Pause Current Ticket

#### 2a: Update context.md — STATUS: PAUSED

Update `tickets/$CURRENT_ID/context.md`:

```markdown
## STATUS: PAUSED
**Paused**: [timestamp]
**Reason**: Switching to $TARGET_ID

## RESUME POINT
[Precise description of where to resume — what's in progress, what comes next.
 Be specific enough that someone else could resume without context.]

Example:
"Server-side validation endpoint created (AdoptionService.validateAdoptionRequest).
 Next: Connect frontend AdoptionForm to use new endpoint —
 see src/components/AdoptionForm.tsx line 47 where the old client validation lives."
```

#### 2b: Append to progress.md

```markdown
---
## [$TIMESTAMP] Paused — switching to $TARGET_ID
**Action**: Context switch
**Reason**: [Why switching — user request / blocker / priority change]
**State**: [Brief state of current work]
**Resume at**: [Same as RESUME POINT above]
```

#### 2c: Commit in-progress work

```bash
git add -A
git commit -m "$CURRENT_ID: WIP — pausing for $TARGET_ID context switch"
```

### Step 3: Update tickets/current.md

```markdown
# Active Ticket

**Ticket**: $TARGET_ID
**Since**: [timestamp]
**Description**: [description if known]
**Previous**: $CURRENT_ID (paused)
```

### Step 4: Resume or Start Target Ticket

#### If target ticket exists:

```bash
ls tickets/$TARGET_ID/
cat tickets/$TARGET_ID/context.md
```

Read the RESUME_POINT or current state.

Append to `tickets/$TARGET_ID/progress.md`:
```markdown
---
## [$TIMESTAMP] Resumed — switching from $CURRENT_ID
**Action**: Context switch
**Previous work on this ticket**: [Brief state from context.md]
**Focus**: [What to work on now]
```

Update `tickets/$TARGET_ID/context.md`:
```markdown
## STATUS: ACTIVE
**Resumed**: [timestamp]
**Current Focus**: [from RESUME_POINT or new direction]
```

Append to `tickets/$TARGET_ID/timeline.md`:
```
| [timestamp] | Resumed from $CURRENT_ID | — |
```

Output:
```
↩️  $CURRENT_ID paused
✅  $TARGET_ID active

Resume point: [description from context.md]
Next step: [first action]
```

#### If target ticket does NOT exist:

Proceed as per `/start-ticket $TARGET_ID`.

---

## FINAL MUST-PASS CHECKLIST

- [ ] Paused ticket context.md STATUS set to PAUSED
- [ ] Paused ticket has RESUME POINT description
- [ ] Paused ticket progress.md has switch entry
- [ ] In-progress work committed
- [ ] tickets/current.md updated to target ticket
- [ ] Target ticket progress.md has resume entry
- [ ] Target ticket context.md STATUS set to ACTIVE
