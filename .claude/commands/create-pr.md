---
name: create-pr
description: Create a GitHub Pull Request from current branch following project standards
allowed-tools: Bash, Read
---

@.claude/rules/git-workflow.md

Create a pull request for the current branch following the PR standards in git-workflow.md.

## Steps

**Step 1** — Gather context:
```bash
git branch --show-current            # current branch
git log main..HEAD --oneline         # commits in this branch
git diff main..HEAD --stat           # files changed
```

**Step 2** — Read the active ticket for context:
- Check `tickets/current.md` for active ticket ID
- Read `tickets/TICKET-ID/plan.md` for objective and acceptance criteria
- Read `tickets/TICKET-ID/context.md` for completion status

**Step 3** — Verify quality gates pass before creating PR:
```bash
# All must pass — do not create PR if any fail
git diff main..HEAD --name-only | grep '\.py$' | xargs python3 -m ruff check
git diff main..HEAD --name-only | grep '\.py$' | xargs python3 -m mypy
```

**Step 4** — Draft PR using this format:

```
Title: TICKET-ID: [brief description matching plan objective]

## Summary
- [What this PR does — 2-3 bullets from acceptance criteria]
- [Second change]
- [Third change]

## Ticket
[TICKET-ID]: [Link to ticket or brief description]

## Changes
- `path/to/file.py`: [What changed and why]
- `path/to/other.py`: [What changed and why]

## Test Plan
- [ ] All unit tests pass
- [ ] [Specific scenario tested manually]
- [ ] No regressions in [related feature]

## Notes
[Any reviewer guidance, known limitations, or follow-up tickets]
```

**Step 5** — Create using GitHub CLI:
```bash
gh pr create --title "TICKET-ID: description" --body "$(cat <<'EOF'
[body from step 4]
EOF
)"
```

## Rules

- Do not create PR if quality gates fail — fix first
- Title must include ticket ID
- Body must include what changed AND why (not just what)
- Self-assign if possible: `gh pr create --assignee @me`
- Add labels matching work type: `bug`, `feature`, `refactor`, `docs`
- Target branch should be `develop` (not `main` directly)
