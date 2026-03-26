# Claude Rules — Navigation Hub

## What Are Rules?

Rules define **how to do things** — standards, validation criteria, and behavioral constraints. They are referenced by commands and embedded in CLAUDE.md.

Unlike Cursor's glob-triggered `.mdc` rules, Claude rules are:
- Read on demand when relevant to a task
- Linked from commands that need them
- Summarized in CLAUDE.md for always-active principles

## Rule Index

### Core Rules (Always Active)
These are embedded directly in `CLAUDE.md` — no need to read these files separately unless you need full detail.

| Rule | Purpose |
|------|---------|
| Communication style | No apologies, no meta-commentary, direct responses |
| Information discipline | Verify before claiming, don't invent |
| Code quality | Zero warnings/errors, single responsibility |
| Change discipline | File-by-file, preserve existing code |

### Domain Rules (Referenced by Commands)

| File | Domain | Invoke When |
|------|--------|------------|
| `ticket-management.md` | Ticket lifecycle | Starting/updating/completing tickets |
| `git-workflow.md` | Git branching | Creating branches, preparing commits |
| `quality-standards.md` | Code quality | Pre-commit, code review, validation |
| `agile-documentation.md` | Agile artifacts | Creating epics, features, stories |
| `clean-code.md` | Code principles | Code review, refactoring |
| `communication-style.md` | AI behavior | Full detail on communication rules |
| `cicd-workflow.md` | CI/CD | Pipeline setup, tag versioning |
| `testing.md` | Testing standards | Writing tests, coverage analysis, test strategy |

## How Rules Work with Commands

```
/start-ticket RAP-123
     ↓
Commands reads: ticket-management.md
     ↓
Follows: Ticket initialization workflow
Creates: plan.md, context.md, progress.md, timeline.md
```

## Rule Authoring Principles

If you need to create or update a rule:

1. **Extract from practice** — Write rules based on patterns you've actually observed, not theoretical ideals
2. **Explicit contracts** — Each rule declares what it reads, writes, and requires
3. **Must-pass checklist** — Every rule ends with 3-7 binary verification items
4. **Stable IDs** — Reference rules by name, never by file path
5. **Version semantics** — Breaking changes = new version

## File Organization

```
.claude/
├── CLAUDE.md                 ← Always-active rules + project config (read first)
├── rules/
│   ├── README.md             ← This file
│   ├── ticket-management.md  ← Full ticket workflow
│   ├── git-workflow.md       ← Git branching strategy
│   ├── quality-standards.md  ← Zero warnings/errors
│   ├── agile-documentation.md← Epic/Feature/Story
│   ├── clean-code.md         ← Code principles
│   ├── communication-style.md← Behavioral AI rules
│   └── cicd-workflow.md      ← CI/CD patterns
├── commands/
│   ├── start-ticket.md       ← /start-ticket
│   ├── complete-ticket.md    ← /complete-ticket
│   ├── switch-ticket.md      ← /switch-ticket
│   ├── update-progress.md    ← /update-progress
│   ├── create-branch.md      ← /create-branch
│   ├── create-story.md       ← /create-story
│   ├── pre-commit-check.md   ← /pre-commit-check
│   └── code-review.md        ← /code-review
└── agents/
    └── ticket-manager.md     ← Autonomous ticket management agent
```
