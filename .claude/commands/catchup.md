---
name: catchup
description: Summarize what has changed in the codebase since last session or a given date/commit
allowed-tools: Bash, Read
---

Produce a concise catch-up brief on codebase changes. Use when resuming after a break or onboarding to work in progress.

## Steps

**Step 1** — Determine the reference point:
- If argument provided (e.g., `/catchup yesterday`, `/catchup 2026-03-20`, `/catchup abc1234`), use that
- Otherwise use: yesterday's date, or the last commit before current session

**Step 2** — Gather change data:
```bash
# Changes since date
git log --since="YYYY-MM-DD" --oneline --no-merges

# Files changed
git diff --stat HEAD~10..HEAD  # or specific range

# Active ticket
cat tickets/current.md 2>/dev/null
```

**Step 3** — Read context for active ticket:
```bash
cat tickets/TICKET-ID/context.md
cat tickets/TICKET-ID/progress.md | tail -30
```

**Step 4** — Produce catch-up brief in this format:

```markdown
## Catch-Up Brief — [Date/Range]

### What Changed
- N commits since [reference point]
- Files modified: [list key files]
- Key changes: [2-4 bullet summaries from commit messages]

### Active Ticket: TICKET-ID
- Status: [ACTIVE/PAUSED]
- Focus: [current focus from context.md]
- Resume at: [RESUME_POINT from context.md, if paused]
- Next step: [first item in Next Steps]

### Outstanding Items
- [ ] [Any open blockers from context.md]
- [ ] [Any TODO/FIXME in recently changed files]

### Recommended First Action
[Single most important thing to do now based on context]
```

## Rules

- Focus on **what matters for continuing work**, not a full git log dump
- If ticket is PAUSED, always show the RESUME_POINT
- If there are open blockers, surface them prominently
- Keep the brief to under 30 lines — scannable, not exhaustive
