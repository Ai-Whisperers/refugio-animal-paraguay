# Claude Commands — Index

Commands are invoked with `/command-name` in Claude Code.

## Ticket Workflow

| Command | Usage | Purpose | Output |
|---------|-------|---------|--------|
| `/start-ticket` | `/start-ticket RAP-42 description` | Initialize a new ticket with full structure | `tickets/RAP-42/` files created, complexity assessment |
| `/complete-ticket` | `/complete-ticket` or `/complete-ticket RAP-42` | Run validation + close ticket | Validation report (pass/fail per level), recap.md |
| `/update-progress` | `/update-progress` | Sync ticket state after work | Updated context.md summary |
| `/switch-ticket` | `/switch-ticket RAP-56` | Safely switch context to another ticket | Pause confirmation + resume point |
| `/execute-plan` | `/execute-plan [plan-file]` | Execute a written implementation plan step by step | Step-by-step execution log with checkpoint results |

## Git & Release

| Command | Usage | Purpose | Output |
|---------|-------|---------|--------|
| `/create-branch` | `/create-branch feature RAP-42 adoption-form` | Create properly named git branch | Branch created, checkout confirmation |
| `/create-pr` | `/create-pr` | Create GitHub PR from current branch | PR URL |
| `/changelog` | `/changelog` | Generate/update CHANGELOG.md from git history | Updated CHANGELOG.md |

## Code Quality

| Command | Usage | Purpose | Output |
|---------|-------|---------|--------|
| `/pre-commit-check` | `/pre-commit-check` | Run all quality gates before committing | Pass/fail per gate (lint, types, tests, security) |
| `/code-review` | `/code-review [file]` | Structured code review against standards | Prioritized findings with severity and fix steps |
| `/refactor` | `/refactor [file]` | Prioritized refactoring analysis for a file | Ranked recommendations with before/after examples |
| `/generate-missing-tests` | `/generate-missing-tests` | Find uncovered code and generate tests | New test file(s), coverage delta |
| `/create-migration` | `/create-migration "description"` | Create a database migration script | Migration SQL file with up/down |

## Agile Documentation

| Command | Usage | Purpose | Output |
|---------|-------|---------|--------|
| `/create-story` | `/create-story` | Create Epic, Feature, or User Story | Markdown artifact in `planning/` |

## Architecture

| Command | Usage | Purpose | Output |
|---------|-------|---------|--------|
| `/adr` | `/adr "Use FastAPI over Django"` | Create Architecture Decision Record | `docs/adr/ADR-NNN.md` |

## Project Documentation

| Command | Usage | Purpose | Output |
|---------|-------|---------|--------|
| `/create-readme` | `/create-readme` | Generate README from current project structure | Updated README.md |
| `/domain-spec` | `/domain-spec` | Document domain objects, enums, and business rules | `docs/domain-spec.md` |
| `/catchup` | `/catchup [date or commit]` | Summarize changes since last session or date | Change summary by area |

---

## Command Shortcuts

These also work:
- `/sync` → `/update-progress`
- `/validate` → `/pre-commit-check`
- `/check` → `/pre-commit-check`
- `/create-epic` → `/create-story` (auto-detects epic mode)
- `/create-feature` → `/create-story` (auto-detects feature mode)

---

## Standard Development Workflow

```
1. Start working:
   /start-ticket RAP-42 adoption request form

2. Create the branch:
   /create-branch feature RAP-42 adoption-request-form

3. Work... work... work...

4. Sync state after each session:
   /update-progress

5. Before committing:
   /pre-commit-check

6. Done with the ticket:
   /complete-ticket
   (validates everything → creates recap → final commit)

7. Create PR:
   /create-pr

8. Update changelog before release:
   /changelog
```

## Files

```
.claude/commands/
├── README.md                  ← This file
├── start-ticket.md            ← /start-ticket
├── complete-ticket.md         ← /complete-ticket
├── update-progress.md         ← /update-progress
├── switch-ticket.md           ← /switch-ticket
├── execute-plan.md            ← /execute-plan
├── create-branch.md           ← /create-branch
├── create-pr.md               ← /create-pr
├── changelog.md               ← /changelog
├── pre-commit-check.md        ← /pre-commit-check
├── code-review.md             ← /code-review
├── refactor.md                ← /refactor
├── generate-missing-tests.md  ← /generate-missing-tests
├── create-migration.md        ← /create-migration
├── create-story.md            ← /create-story
├── create-readme.md           ← /create-readme
├── domain-spec.md             ← /domain-spec
├── catchup.md                 ← /catchup
└── adr.md                     ← /adr
```
