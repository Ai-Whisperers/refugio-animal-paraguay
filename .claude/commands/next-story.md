# Command: /next-story
**Usage**: `/next-story`
**Example**: `/next-story`

---

## What This Does

Picks up the next READY story from `planning/QUEUE.md`, assigns a ticket ID, creates a branch, and begins autonomous implementation. This is the **autonomous development loop** — after completing a story, run `/next-story` again to keep working.

**Rules applied**: `ticket-management.md`, `git-workflow.md`, `quality-standards.md`, `testing.md`

---

## Workflow

### Step 1: Read the Queue

```bash
cat planning/QUEUE.md
```

Find the **first story** in the current sprint with status `READY`. If no READY stories exist in the current sprint, check the next sprint. If all stories are DONE or BLOCKED, report completion.

### Step 2: Identify the Story

From the queue entry, extract:
- **Story number** and name
- **Epic reference** (e.g., EPIC-1 S06)
- **Story points**
- **Track** (Backend / Frontend)

### Step 3: Read the Story Definition

Navigate to the story file in `planning/epics/` and read:
- `STORY.md` — acceptance criteria, tasks, dependencies
- Parent `EPIC.md` — context and scope

If the story has tasks defined, read those too.

### Step 4: Assign a Ticket ID

Use the ticket ID allocation table in QUEUE.md:
- V1: RAP-011 to RAP-030
- V2: RAP-031 to RAP-050

Check `tickets/` directory to find the next unused RAP-NNN ID:

```bash
ls tickets/ | grep -oP 'RAP-\d+' | sort -t'-' -k2 -n | tail -1
```

If no tickets exist yet, start at the range minimum for the current version.

### Step 5: Load Relevant Skills

Based on the story's domain, read the appropriate skill files:

| Domain | Skill to Load |
|--------|--------------|
| API endpoints | `.claude/skills/fastapi-patterns.md`, `.claude/skills/rest-api-patterns.md` |
| Database/schema | `.claude/skills/postgresql-patterns.md` |
| Auth/security | `.claude/skills/payment-patterns.md` |
| Testing | `.claude/skills/testing-patterns.md` |
| EU/donations | `.claude/skills/eu-donation-patterns.md`, `.claude/skills/payment-patterns.md` |
| Python general | `.claude/skills/python-patterns.md` |

### Step 6: Initialize the Ticket

Run the `/start-ticket` workflow:
1. Create `tickets/RAP-NNN/` directory
2. Generate `plan.md` from the story's acceptance criteria
3. Create `context.md`, `progress.md`, `timeline.md`, `references.md`
4. Set `tickets/current.md` to the new ticket

### Step 7: Create the Branch

```bash
git checkout develop
git pull origin develop 2>/dev/null || true
git checkout -b feature/RAP-NNN-brief-description
```

Branch name: `feature/RAP-NNN-` + hyphenated story name (3-5 words max).

### Step 8: Implement

Follow the plan phases. For each phase:

1. **Write code** — follow clean-code.md principles
2. **Write tests** — unit tests first, then integration if applicable
3. **Run quality gates**:
   ```bash
   make lint
   make type-check
   make format
   make test
   make security
   ```
4. **Commit** — small, focused commits with `RAP-NNN: <description>`
5. **Update progress.md** — log what was done, decisions made

### Step 9: Validate Completion

Run the `/complete-ticket` workflow:
1. All acceptance criteria met (check each one)
2. All quality gates pass (`make all-checks`)
3. Coverage not decreased
4. Create `recap.md`
5. Update QUEUE.md — mark the story as DONE

### Step 10: Loop

After completion, output:

```
Story #N complete. Next READY story: #M [name]
Run /next-story to continue, or review the work first.
```

---

## Autonomous Execution Rules

1. **Never skip quality gates** — every commit must pass `make all-checks`
2. **Never start a BLOCKED story** — check dependencies in QUEUE.md first
3. **Commit often** — at least once per logical unit of work
4. **Update QUEUE.md** when completing a story (move to Done section)
5. **Read before writing** — always read existing code before modifying
6. **Test edge cases** — empty states, errors, permissions, invalid input
7. **Follow existing patterns** — look at delivered code (RAP-001 through RAP-010) for conventions

## Error Recovery

If a quality gate fails:
1. Read the error message carefully
2. Fix the issue
3. Re-run the gate
4. If stuck after 3 attempts, log the blocker in `context.md` and move to the next READY story

If a dependency is missing:
1. Check if the dependency is another story in the queue
2. If yes, mark current story BLOCKED and pick next READY story
3. If it's an external dep (library, service), install/configure it

---

## FINAL MUST-PASS CHECKLIST

Before marking a story DONE:
- [ ] All acceptance criteria from STORY.md verified
- [ ] `make all-checks` passes (lint, types, format, tests, security)
- [ ] Coverage >= 80%
- [ ] All commits reference ticket ID (RAP-NNN: ...)
- [ ] recap.md created with outcome and validation evidence
- [ ] QUEUE.md updated — story marked DONE
- [ ] No TODO/FIXME left for this ticket
- [ ] Branch ready for PR
