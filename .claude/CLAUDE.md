# CLAUDE.md — Refugio Animal Paraguay

## Project Overview

**Refugio Animal Paraguay** is an animal shelter management platform serving the Paraguayan context, with European funding network integration. The platform handles adoptions, donations (including international/EU donors), animal records, volunteer coordination, and shelter operations.

**Owner context**: Dutch owner relocating to Paraguay. European donor network is critical — donation flows and reporting must reflect EU standards and currency handling (EUR + PYG).

---

## Current Phase

**Phase 0 — Foundation**: Documentation, planning, framework setup. **COMPLETED.**
**Phase 1 — Data Layer**: PostgreSQL schema, Alembic migrations, seed data. **COMPLETED** (RAP-001, RAP-002).
**Phase 2 — API Scaffold**: FastAPI routes, auth, basic CRUD. **COMPLETED** (RAP-003 through RAP-010).

**Phase 3 — Feature Expansion (next)**: Medical records, volunteer management, notifications, frontend.

**Current state**: 30 source files, 18 test files (95 tests passing), full CRUD APIs (animals, adopters, adoption requests, donors, donations), JWT auth with roles, animal photo gallery, Stripe donations, Docker containerization with auto-migrations. 4 Alembic migrations applied.

---

## How This System Works

This `.claude/` directory provides a structured framework for AI-assisted development:

```
User Request
    ↓
Commands (.claude/commands/)   ← What to do (task workflows, invoke with /command-name)
    ↓
Rules (.claude/rules/)         ← How to do it (standards, validation, constraints)
    ↓
Output / Action
```

**Commands** are task workflows: "create a user story", "start a ticket", "do a code review"
**Rules** are behavioral constraints that always apply or are referenced by commands

---

## Always-Active Behavioral Rules

These apply to every interaction — no exceptions:

### Communication Style
- **No apologies**: Never say "sorry", "I apologize", "my mistake". State corrections directly.
- **No meta-commentary**: Don't say "Great question!" or "I understand that you want to...". Just do it.
- **No summaries after work**: Don't recap what you just did. The diff speaks for itself.
- **No unnecessary confirmations**: Don't ask "shall I proceed?" for low-risk actions. Just proceed.
- **Direct corrections**: When wrong, correct without apology. When asked to fix, fix it.

### Information Discipline
- **Verify before claiming**: Don't assert something exists (function, file, API) without reading it first.
- **No inventions**: Don't invent features, behaviors, or requirements not explicitly stated.
- **Read before modifying**: Always read a file before editing it — understand what's there.
- **Preserve existing code**: Only change what's necessary. Don't refactor adjacent code.

### Code Quality
- **Zero warnings, zero errors**: Code is not done until all linters, type checks, and tests pass clean.
- **Single responsibility**: Each function does one thing. Split if you need a comment explaining what it does.
- **DRY**: Extract repeated logic. Don't duplicate business rules across files.
- **Constants over magic values**: Named constants, not inline strings/numbers.
- **Meaningful names**: Names reveal purpose, not implementation. No `data`, `temp`, `x`.

### Change Discipline
- **File-by-file**: Make one logical change at a time. Document intent of each change.
- **Single chunk edits**: Apply edits in one coherent block per file, not scattered small edits.
- **No whitespace churn**: Don't propose whitespace-only changes or reformatting of unrelated code.

---

## Ticket Workflow (Summary)

Full rules: `.claude/rules/ticket-management.md`
Commands: `/start-ticket`, `/complete-ticket`, `/switch-ticket`, `/update-progress`

A ticket is a **small, short-lived work unit** with structured documentation:

```
tickets/TICKET-ID/
  plan.md        ← Objective, acceptance criteria, complexity assessment
  context.md     ← Current state, focus, blockers, next steps (live document)
  progress.md    ← Append-only chronological log of actions/decisions
  timeline.md    ← Timestamp tracking for session reconstruction
  references.md  ← File paths and key references
  recap.md       ← Outcome summary (created at closure)
  rca.md         ← Root cause analysis (defects only)

tickets/current.md  ← Active ticket ID (local only, gitignored)
```

**Completion discipline**: When user says "done" or "finished" — STOP. Run full validation before accepting. Never close a ticket without verification evidence in progress.md.

**Complexity assessment** (required when creating plan.md):
- **Simple Fix**: Single root cause, ≤3 files, ≤10 lines changed → direct implementation
- **Complex**: Any: multiple causes, >3 files, >10 lines, architectural changes → phased approach

---

## Git Workflow (Summary)

Full rules: `.claude/rules/git-workflow.md`
Commands: `/create-branch`

```
main         ← Production-ready only
develop      ← Integration branch
feature/*    ← New features (branch from develop)
fix/*        ← Bug fixes (branch from develop)
hotfix/*     ← Critical production fixes (branch from main)
release/*    ← Release preparation
```

**Branch naming**: `feature/RAP-123-brief-description` (ticket ID + hyphenated description)
**Commits**: Reference ticket ID in every commit message: `RAP-123: Add adoption request form`

---

## Quality Standards (Summary)

Full rules: `.claude/rules/quality-standards.md`
Commands: `/pre-commit-check`, `/code-review`

Before every commit, ALL must pass:
1. **Build/compile** — zero errors
2. **Linting** — zero warnings
3. **Type checking** — zero type errors
4. **Tests** — all pass, coverage maintained
5. **Security** — no exposed secrets, no vulnerable deps

**Diagnostic message format** (when writing error messages or validation scripts):
- **WHAT**: What is wrong, precisely
- **WHY**: Why this is a problem
- **HOW**: Exact steps to fix it

---

## Agile Documentation (Summary)

Full rules: `.claude/rules/agile-documentation.md`
Commands: `/create-story`, `/create-epic`

```
Epic (2+ sprints)
  └── Feature (1-2 sprints)
       └── User Story (single sprint)
            └── Task (hours)
```

**User story format**: "As a [role], I want [goal] so that [benefit]"
**Acceptance criteria**: Given/When/Then or bullet list of testable conditions
**Definition of Done**: Tests pass, docs updated, PR reviewed, deployed to staging

---

## Rule Navigation

| Domain | Rule File | Commands |
|--------|-----------|---------|
| Ticket workflow | `.claude/rules/ticket-management.md` | `/start-ticket`, `/complete-ticket`, `/switch-ticket`, `/update-progress` |
| Git branching | `.claude/rules/git-workflow.md` | `/create-branch` |
| Code quality | `.claude/rules/quality-standards.md` | `/pre-commit-check`, `/code-review` |
| Agile docs | `.claude/rules/agile-documentation.md` | `/create-story`, `/create-epic` |
| Clean code | `.claude/rules/clean-code.md` | `/code-review` |
| Communication | Embedded above | — |

## Skills (Domain Knowledge)

Domain knowledge loaded on demand via skills:

| Skill | File | Load When |
|-------|------|-----------|
| EU donations & GDPR | `.claude/skills/eu-donation-patterns.md` | Any donation, EUR, GDPR, IBAN work |
| Payment processing | `.claude/skills/payment-patterns.md` | Stripe, SEPA, IBAN, EUR/PYG currency, idempotency |
| FastAPI patterns | `.claude/skills/fastapi-patterns.md` | Building REST endpoints, schemas, dependencies, testing |
| Paraguayan animal law | `.claude/skills/paraguayan-animal-law.md` | Adoption, registration, legal, vaccination work |
| Testing patterns | `.claude/skills/testing-patterns.md` | Writing tests, pytest, coverage, fixtures, mocking |
| REST API patterns | `.claude/skills/rest-api-patterns.md` | API design, endpoints, validation, pagination |
| PostgreSQL patterns | `.claude/skills/postgresql-patterns.md` | Schema design, indexing, migrations, query optimization |
| Python patterns | `.claude/skills/python-patterns.md` | Async, retry, logging, type hints, dataclasses |

## Specialist Agents

| Agent | File | Use For |
|-------|------|---------|
| Ticket manager | `.claude/agents/ticket-manager.md` | Autonomous ticket lifecycle management |
| Schema designer | `.claude/agents/schema-designer.md` | PostgreSQL schema design with Refugio conventions |
| Security auditor | `.claude/agents/security-auditor.md` | Vulnerability review (PII, SQL injection, GDPR) |
| Test writer | `.claude/agents/test-writer.md` | Generate unit/integration tests for a module |
| Doc writer | `.claude/agents/doc-writer.md` | Add/improve docstrings and API documentation |
| Refactoring advisor | `.claude/agents/refactoring-advisor.md` | Structural analysis and prioritized refactoring plan |

## Extended Thinking

For complex architectural or domain decisions, prefix your prompt with `ultrathink`:
```
ultrathink: what's the best data model for handling EUR and PYG donations with different tax reporting?
```
Activates deeper reasoning. Use for architecture, data model design, and complex compliance questions.

---

## Project Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.12 + FastAPI | Async-first, Pydantic v2 schemas |
| Database | PostgreSQL 16 | SQLAlchemy 2.x ORM, Alembic migrations |
| Auth | JWT (HTTP Bearer) | fastapi-users or custom; roles: staff, admin, adopter |
| Payments | Stripe (EUR/SEPA) | EU/NL donors; PYG cash handling TBD |
| Frontend | TBD | Not yet started |
| Hosting | TBD | EU-West region preferred (donor latency); Paraguay secondary |
| CI/CD | GitHub Actions | Pipeline definition TBD in Phase 2 |
| Email | TBD | Transactional email for notifications |

---

## OPSEC Rules

- **Never** commit `.env` files, credentials, API keys, or tokens
- **Never** include real donor data, animal records, or personal info in ticket docs or code comments
- **Never** expose internal server names, IPs, or infrastructure details in logs/tickets
- Mask secrets after first 8 characters in any output

---

## Quick Reference — Common Workflows

| Task | Command | Rules Applied |
|------|---------|--------------|
| Start new ticket | `/start-ticket RAP-123` | ticket-management.md |
| Update ticket state | `/update-progress` | ticket-management.md |
| Complete a ticket | `/complete-ticket` | ticket-management.md (with validation) |
| Switch tickets | `/switch-ticket RAP-456` | ticket-management.md |
| Create feature branch | `/create-branch feature RAP-123 description` | git-workflow.md |
| Pre-commit validation | `/pre-commit-check` | quality-standards.md |
| Code review | `/code-review` | quality-standards.md, clean-code.md |
| Create user story | `/create-story` | agile-documentation.md |
| Create PR | `/create-pr` | git-workflow.md |
| Update changelog | `/changelog` | cicd-workflow.md |
| Analyze refactoring | `/refactor [file]` | clean-code.md |
| Generate tests | `/generate-missing-tests` | testing.md |
| Create migration | `/create-migration` | quality-standards.md |
| Generate README | `/create-readme` | — |
| Extract domain spec | `/domain-spec` | — |
| Catch up on changes | `/catchup` | — |
| Execute a plan | `/execute-plan [plan-file]` | ticket-management.md |
| Record architecture decision | `/adr "Decision title"` | — |

---

## Project Rules Index

- `.claude/rules/README.md` — Full rules navigation
- `.claude/rules/ticket-management.md` — Ticket lifecycle, files, validation
- `.claude/rules/git-workflow.md` — Branching, naming, lifecycle
- `.claude/rules/quality-standards.md` — Zero warnings/errors, diagnostics
- `.claude/rules/agile-documentation.md` — Epic/Feature/Story structure
- `.claude/rules/clean-code.md` — Code quality principles
- `.claude/rules/communication-style.md` — AI behavioral rules
- `.claude/rules/testing.md` — Testing standards, coverage requirements
- `.claude/rules/cicd-workflow.md` — CI/CD pipeline, tag versioning

## Exemplars (Calibration References)

Good/bad examples that calibrate output quality — read when creating the corresponding artifact:

| Exemplar | File | Use When |
|----------|------|----------|
| Good user story | `.claude/exemplars/agile/user-story-good.md` | Writing user stories |
| Bad user story patterns | `.claude/exemplars/agile/user-story-bad.md` | Reviewing user stories |
| Good epic | `.claude/exemplars/agile/epic-good.md` | Writing epics |
| Good feature | `.claude/exemplars/agile/feature-good.md` | Writing features |
| Good ticket plan | `.claude/exemplars/ticket/plan-good.md` | Creating ticket plans |
| Bad ticket plan patterns | `.claude/exemplars/ticket/plan-bad.md` | Reviewing ticket plans |
| Python error handling | `.claude/exemplars/python/error-handling.py` | Writing error handling |
| Tag versioning | `.claude/exemplars/cicd/tag-versioning.md` | Setting up CI/CD releases |
| Good ADR | `.claude/exemplars/adr/adr-good.md` | Writing Architecture Decision Records |

---

*Last updated: 2026-03-26*
*Version: 1.4.0*
