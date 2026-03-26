---
name: execute-plan
description: Execute a written implementation plan step by step with checkpoints
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

@.claude/rules/ticket-management.md
@.claude/rules/quality-standards.md

Execute a written implementation plan one step at a time. Pause at checkpoints to show what was done and confirm before continuing.

## Steps

**Step 1** — Load the plan:
- If argument provided: read the specified plan file
- Otherwise: read `tickets/$(cat tickets/current.md 2>/dev/null)/plan.md`
- If no plan found: stop and ask user where the plan is

**Step 2** — Parse the plan:
- Extract numbered steps or phases
- Identify acceptance criteria (for completion validation later)
- Show the full step list to the user:

```markdown
## Plan: [name]
Steps to execute:
1. [Step 1 title]
2. [Step 2 title]
3. [Step 3 title]

Starting with Step 1...
```

**Step 3** — Execute each step:
For each step:
1. Read any files mentioned in the step before modifying them
2. Make the change
3. Run relevant validation (compile, lint, test the affected code)
4. Report result:

```markdown
### ✅ Step N complete — [title]
- Changed: [file:line — what changed]
- Validation: [result of lint/test run]
- Next: Step N+1 — [title]
```

**Step 4** — Checkpoint every 3 steps or at phase boundaries:

```markdown
## Checkpoint — Steps 1-3 complete

What was done:
- [Step 1]: [one line]
- [Step 2]: [one line]
- [Step 3]: [one line]

Current state: [brief description]
Next steps: Steps 4-6

Continue? (say "continue" or "stop")
```

**Step 5** — On completion:
- Run full quality gate (all lint, type check, tests)
- Show acceptance criteria from plan with pass/fail status
- Update `context.md` if this is part of a ticket

## Rules

- Never skip a step without explaining why
- If a step fails: stop and show the error — do not try to work around it silently
- If a step is ambiguous: ask, do not invent interpretation
- Keep each step atomic — one logical change
- Run validation after each step, not just at the end
- If quality gate fails at the end: do not mark complete
