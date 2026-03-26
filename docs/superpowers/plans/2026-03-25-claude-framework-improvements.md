# Claude Framework Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the `.claude/` framework so AI agents can work autonomously without guessing stack, phase, or boundaries.

**Architecture:** Eight targeted improvements to CLAUDE.md, rules, skills, agents, and commands. No application code. All changes are documentation edits and file additions.

**Tech Stack:** Markdown edits only. No build tools required.

---

## File Map

| File | Change Type | Task |
|------|------------|------|
| `.claude/CLAUDE.md` | Modify | Task 1 |
| `docs/adr/ADR-001-tech-stack.md` | Create | Task 2 |
| `tickets/RAP-001/` (5 files) | Create | Task 3 |
| `.claude/rules/ticket-management.md` | Trim | Task 4a |
| `.claude/rules/git-workflow.md` | Trim | Task 4b |
| `.claude/rules/quality-standards.md` | Trim | Task 4c |
| `.claude/rules/agile-documentation.md` | Trim | Task 4d |
| `.claude/rules/clean-code.md` | Trim | Task 4e |
| `.claude/rules/communication-style.md` | Trim | Task 4f |
| `.claude/rules/cicd-workflow.md` | Trim | Task 4g |
| `.claude/rules/testing.md` | Trim | Task 4h |
| `.claude/skills/fastapi-patterns.md` | Add boundary | Task 5 |
| `.claude/skills/python-patterns.md` | Add boundary | Task 5 |
| `.claude/skills/rest-api-patterns.md` | Add boundary | Task 5 |
| `.claude/skills/postgresql-patterns.md` | Add boundary | Task 5 |
| `.claude/agents/ticket-manager.md` | Add dispatch contract | Task 6 |
| `.claude/agents/schema-designer.md` | Add dispatch contract | Task 6 |
| `.claude/agents/security-auditor.md` | Add dispatch contract | Task 6 |
| `.claude/agents/test-writer.md` | Add dispatch contract | Task 6 |
| `.claude/agents/doc-writer.md` | Add dispatch contract | Task 6 |
| `.claude/agents/refactoring-advisor.md` | Add dispatch contract | Task 6 |
| `.claude/commands/README.md` | Add Output column | Task 7 |

---

## Task 1: CLAUDE.md — Tech Stack + Current Phase

**Files:**
- Modify: `.claude/CLAUDE.md`

### What to change

**A) Replace the Project Tech Stack table** (lines 192–204) with this locked stack:

```markdown
## Project Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.12 + FastAPI | Async-first, Pydantic v2 schemas |
| Database | PostgreSQL 16 | SQLAlchemy 2.x ORM, Alembic migrations |
| Auth | JWT (HTTP Bearer) | fastapi-users or custom; roles: staff, admin, adopter |
| Payments | Stripe (EUR/SEPA) | EU/NL donors; PYG cash handling TBD |
| Frontend | TBD | Not yet started |
| Hosting | TBD | EU-West region preferred (donor latency); Paraguay secondary |
| CI/CD | GitHub Actions | |
| Email | TBD | Transactional email for notifications |
```

**B) Insert a Current Phase section** immediately after the Project Overview block (after line 8, before "---"):

```markdown
## Current Phase

**Phase 0 — Foundation (active)**: Documentation, planning, and framework setup only.
No application code exists. Tech stack decided (see above). First ticket pending.

**Phase 1 — Data Layer (next)**: PostgreSQL schema, Alembic migrations, seed data.
**Phase 2 — API Scaffold (future)**: FastAPI routes, auth, basic CRUD.
```

- [ ] **Step 1: Read the current CLAUDE.md**

```bash
cat -n .claude/CLAUDE.md | head -15
```

- [ ] **Step 2: Insert Current Phase section after line 8**

Add the Current Phase block after `**Owner context**: Dutch owner relocating...` line, before the first `---`.

- [ ] **Step 3: Replace Tech Stack table**

Replace the `## Project Tech Stack` section (including the `*Update this section*` note) with the locked table above.

- [ ] **Step 4: Update version and date at bottom**

Change `*Version: 1.2.0*` → `*Version: 1.3.0*` and `*Last updated: 2026-03-25*` → current date.

- [ ] **Step 5: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: lock tech stack and add current phase to CLAUDE.md"
```

---

## Task 2: Create ADR-001 — Tech Stack Decision

**Files:**
- Create: `docs/adr/ADR-001-tech-stack.md`
- Modify: `docs/adr/README.md`

- [ ] **Step 1: Create ADR-001**

Create `docs/adr/ADR-001-tech-stack.md` with this content:

```markdown
# ADR-001: Core Tech Stack Selection

**Date**: 2026-03-25
**Status**: Accepted
**Deciders**: Project owner

---

## Context

Refugio Animal Paraguay needs a backend stack for an animal shelter management platform with:
- EU donor integration (SEPA, IBAN, GDPR compliance)
- Dual currency: EUR (European donors) + PYG (local Paraguayan)
- Animal records, adoptions, volunteer coordination
- Dutch owner context — EU-standard tooling preferred

## Decision

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.12 | Owner familiarity; strong async support; best-in-class Stripe/GDPR libraries |
| Framework | FastAPI | Async-native; Pydantic v2 integration; auto-generates OpenAPI docs; faster than Django REST for API-only backends |
| ORM | SQLAlchemy 2.x | Mature; supports async; works with Alembic for migrations |
| Migrations | Alembic | Standard SQLAlchemy migration tool; reversible migrations required |
| Database | PostgreSQL 16 | ACID compliance critical for financial data; UUID support; JSONB for flexible fields |
| Auth | JWT (HTTP Bearer) | Stateless; suitable for future mobile/third-party integrations |
| Payments | Stripe | EU-compliant; supports SEPA Direct Debit for recurring EU donors; PYG-to-EUR conversion path |
| CI/CD | GitHub Actions | Repository already on GitHub; no additional infra cost |

## Alternatives Considered

**Django REST Framework**: Rejected — heavier, sync-first, more boilerplate for pure API backend.
**SQLModel**: Considered as a SQLAlchemy + Pydantic shortcut, but SQLAlchemy 2.x + Pydantic v2 directly gives more control and is better documented.
**Auth0 / Supabase Auth**: Deferred — adds external dependency; JWT + fastapi-users is sufficient for MVP.

## Consequences

- All skills files (fastapi-patterns, postgresql-patterns, python-patterns) are now canonical for this stack.
- Frontend remains TBD — decouple from backend decisions.
- PYG payment processor for local donors still to be decided (ADR-002 when ready).
- Hosting TBD — EU-West region preferred for donor latency (ADR-003 when ready).

## Related ADRs

- ADR-002 (pending): PYG payment processor
- ADR-003 (pending): Hosting platform selection
```

- [ ] **Step 2: Update docs/adr/README.md Record Index table**

Replace the `| — | *(no ADRs yet...)* | — | — |` row with:

```markdown
| ADR-001 | Core Tech Stack Selection | Accepted | 2026-03-25 |
```

Also remove the "Pending Decisions" section items that are now resolved (Backend framework, Database + ORM, CI/CD), keeping only the still-TBD items.

- [ ] **Step 3: Commit**

```bash
git add docs/adr/ADR-001-tech-stack.md docs/adr/README.md
git commit -m "docs: add ADR-001 formalizing core tech stack selection"
```

---

## Task 3: Create First Ticket — RAP-001

**Files:**
- Create: `tickets/RAP-001/plan.md`
- Create: `tickets/RAP-001/context.md`
- Create: `tickets/RAP-001/progress.md`
- Create: `tickets/RAP-001/timeline.md`
- Create: `tickets/RAP-001/references.md`
- Modify: `tickets/current.md`

**Scope**: The first real ticket is the animal database schema — smallest useful slice from the highest-priority epic (EPIC-2: Adoption Process, priority 95). Gives the schema-designer agent something to work on and validates the ticket system.

- [ ] **Step 1: Create tickets/RAP-001/plan.md**

```markdown
# RAP-001 Plan

## Objective
Design and create the core PostgreSQL schema for animals, adopters, and adoption requests.

## Description
The animal schema is the foundation for the entire platform. It must support animal records
(species, status, medical history), adopter profiles, and the adoption request lifecycle.
Schema must follow Refugio conventions: UUID PKs, TIMESTAMPTZ, status enums, soft-delete via
status rather than deleted_at.

## Acceptance Criteria
- [ ] `animals` table created with: id, name, species, status enum, birth_date, description, created_at, updated_at
- [ ] `adopters` table created with: id, full_name, email (unique), phone, address, gdpr_consent_at, created_at
- [ ] `adoption_requests` table with: id, animal_id (FK), adopter_id (FK), status enum, submitted_at, decided_at, notes
- [ ] EXCLUDE constraint: one active request per animal (prevents duplicate pending requests)
- [ ] Indexes: animals(status), adoption_requests(animal_id), adoption_requests(adopter_id), adoption_requests(status)
- [ ] Alembic migration file created and named descriptively
- [ ] Seed data script creates 5 sample animals + 2 adopters
- [ ] Schema validated against Refugio conventions (UUIDs, TIMESTAMPTZ, snake_case tables)

## Complexity Assessment
**Track**: Complex Implementation

### Assessment result
Complex — affects 3 tables, multiple constraints, Alembic migration, seed data. Phased approach: schema → migration → seed.

## Approach
1. Design schema using schema-designer agent
2. Write Alembic migration
3. Write seed data script
4. Validate against conventions

## Dependencies
- Depends on: tech stack decision (resolved in ADR-001)
- Blocked by: none

## Risks
- Risk: Animal status enum design may need expansion → Mitigation: use VARCHAR with check constraint initially, migrate to proper enum once status values are stable
```

- [ ] **Step 2: Create tickets/RAP-001/context.md**

```markdown
# RAP-001 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-25

## Current Focus
Ticket initialized. Ready to start schema design.

## Technical State
- No application code exists yet
- Database: PostgreSQL 16 decided (ADR-001)
- ORM: SQLAlchemy 2.x + Alembic decided (ADR-001)

## Next Steps
1. Use schema-designer agent to produce CREATE TABLE statements
2. Review schema against acceptance criteria
3. Create Alembic migration
4. Write seed data script

## Blockers
None.

## Key Decisions Made
- UUID PKs for all tables (prevents enumeration)
- Status enum approach for animal lifecycle (not soft-delete)
- GDPR consent timestamp on adopters (EU requirement)

## RESUME POINT
Start with schema design — invoke schema-designer agent with domain description.
```

- [ ] **Step 3: Create tickets/RAP-001/progress.md**

```markdown
# RAP-001 Progress Log

---
## [2026-03-25] Ticket Initialized
**Action**: Created ticket RAP-001 — animal core schema
**Findings**: ADR-001 confirmed tech stack. No blockers.
**Next**: Schema design with schema-designer agent
```

- [ ] **Step 4: Create tickets/RAP-001/timeline.md**

```markdown
# RAP-001 Timeline

| Timestamp | Event | Duration |
|-----------|-------|---------|
| 2026-03-25 | Ticket created | — |

## Session Summary
- Total sessions: 1 (initialization only)
- Estimated hours: TBD
```

- [ ] **Step 5: Create tickets/RAP-001/references.md**

```markdown
# RAP-001 References

## Key Files
- Schema output: `src/db/migrations/` (to be created)
- Seed script: `src/db/seeds/animals.py` (to be created)
- Schema designer agent: `.claude/agents/schema-designer.md`

## Related Skills
- `.claude/skills/postgresql-patterns.md` — schema conventions
- `.claude/skills/eu-donation-patterns.md` — GDPR consent on adopters

## Related ADRs
- `docs/adr/ADR-001-tech-stack.md` — PostgreSQL + Alembic decision

## Domain Reference
- `.claude/skills/paraguayan-animal-law.md` — legal requirements affecting animal records
```

- [ ] **Step 6: Update tickets/current.md**

Set content to:
```
RAP-001
```

- [ ] **Step 7: Commit**

```bash
git add tickets/RAP-001/ tickets/current.md
git commit -m "RAP-001: Initialize ticket — animal core database schema"
```

---

## Task 4: Trim Rules Files (30–40% reduction)

**Trimming principle**: Keep templates, file structures, checklists, decision criteria, and code examples. Remove: "Purpose & Scope" preamble prose, "why this matters" explanations, philosophical justifications, redundant anti-pattern explanations that repeat what the examples already show.

Each rule file is a separate commit.

### Task 4a: ticket-management.md

**Remove**:
- The entire "Purpose & Scope" section (lines explaining what it applies to, what it doesn't — this is in CLAUDE.md already)
- The "Inputs (Contract)" and "Outputs (Contract)" sections — the file structure diagram makes this redundant
- The "Behavioral Rules for AI Agents" section (Always/Never bullets) — these are already embedded in the lifecycle workflow steps
- OPSEC Rules section — covered in CLAUDE.md

**Keep**: All 7 file structure templates, lifecycle workflow phases 1–4, switching discipline, complexity tracks, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] Verify checklist and all templates remain intact
- [ ] `git commit -m "docs: trim ticket-management.md — remove prose, keep templates"`

### Task 4b: git-workflow.md

**Remove**:
- "Purpose & Scope" intro paragraph
- The "Inputs/Outputs" contract section
- Branch purposes table (redundant with the branch structure diagram + branch naming table)
- "Branch Lifecycle" prose paragraphs before the numbered steps (the steps themselves are sufficient)

**Keep**: Branch structure diagram, naming pattern + examples + anti-patterns, commit format + examples + anti-patterns, PR body template, PR checklist, tag strategy, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim git-workflow.md — remove prose, keep patterns and examples"`

### Task 4c: quality-standards.md

**Remove**:
- "Purpose & Scope" intro
- The "When to Fix vs Suppress" philosophical paragraphs (keep the code examples)
- "Quality Anti-Patterns" section (already covered by checklists)

**Keep**: Quality gates table, pre-commit validation workflow steps, suppression code examples, WHAT+WHY+HOW diagnostic format + examples, tool-specific commands, coverage section, security standards, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim quality-standards.md — keep gates, examples, checklist"`

### Task 4d: agile-documentation.md

**Remove**:
- "Purpose & Scope" intro
- "Sprint Ceremonies" section (Scrum rituals are standard; this adds no project-specific value)
- The "Story Splitting Patterns" section title text (keep the examples, remove the intro prose for each pattern)

**Keep**: Full hierarchy + sizing guide, Epic/Feature/Story templates, Refugio-specific roles table, story anti-patterns, story splitting examples, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim agile-documentation.md — remove ceremony prose, keep templates"`

### Task 4e: clean-code.md

**Remove**:
- "Purpose & Scope" intro
- The explanatory prose before each principle (the code examples are self-explanatory)
- "Refactoring Guidelines" section — covered by the `/refactor` command

**Keep**: All 8 principle code examples (bad/good pairs), anti-patterns section with code examples, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim clean-code.md — keep examples, remove prose"`

### Task 4f: communication-style.md

**Remove**:
- "Purpose & Scope" intro
- All explanatory paragraphs before the ❌/✅ examples — the examples are sufficient

**Keep**: All ❌/✅ example blocks for each behavioral rule, "Correctness Over Compliance" section (has unique content), "Scope Discipline" section, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim communication-style.md — keep examples, remove prose"`

### Task 4g: cicd-workflow.md

**Remove**:
- "Purpose & Scope" intro
- Detailed prose descriptions before each stage's yaml block (the yaml is self-documenting)
- "Monitoring & Alerting" section (too generic, no project-specific values)

**Keep**: 5-stage architecture diagram, stage YAML blocks with fail conditions, branch behavior table, tag format table, tag type table, local validation script, environment tier table, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim cicd-workflow.md — remove prose, keep pipeline spec"`

### Task 4h: testing.md

**Remove**:
- "Purpose & Scope" intro
- "Core Principles" bullet list (covered by code examples that follow)
- "What NOT to Test" section — too subjective, causes confusion

**Keep**: Test pyramid diagram, coverage requirements table, test file structure, naming examples, AAA pattern example, fixture example, mocking rules + code examples, integration test example, async test example, test anti-patterns, FINAL CHECKLIST.

- [ ] Read the full file
- [ ] Apply edits
- [ ] `git commit -m "docs: trim testing.md — keep pyramid, examples, coverage table"`

---

## Task 5: Add Trigger Boundaries to Generic Tech Skills

**Problem**: fastapi-patterns, python-patterns, rest-api-patterns, postgresql-patterns have no `not-when:` boundary. They burn tokens on knowledge already in training data.

**Solution**: Add `not-when:` frontmatter field and a one-line "project-specific knowledge" note at the top of each skill explaining what's unique about the Refugio context.

**Files:**
- Modify: `.claude/skills/fastapi-patterns.md`
- Modify: `.claude/skills/python-patterns.md`
- Modify: `.claude/skills/rest-api-patterns.md`
- Modify: `.claude/skills/postgresql-patterns.md`

- [ ] **Step 1: Update fastapi-patterns.md frontmatter**

The file currently starts with `# Skill: FastAPI Patterns` and a `**Load when**: ...` line (no YAML frontmatter). Add YAML frontmatter at the top:

```markdown
---
name: fastapi-patterns
description: Refugio-specific FastAPI structure, project layout, and dependency wiring — NOT generic FastAPI docs
load-when: Building FastAPI routes, dependency injection, lifespan events, or background tasks FOR THIS PROJECT
not-when: General Python questions, schema design, database queries, payment logic — use domain skills instead
project-specific: src/ layout, lifespan DB pool setup, pagination cursor pattern, error response schema
---
```

- [ ] **Step 2: Update python-patterns.md**

The file has existing YAML frontmatter (lines 1-5). Update it to add `not-when`:

```yaml
---
name: python-patterns
description: Python async patterns, retry logic, structured logging, type hints, dataclasses, and common idioms
load-when: Python async/await, retry logic, structured logging, type safety in THIS codebase
not-when: FastAPI routing (use fastapi-patterns), SQL queries (use postgresql-patterns), payment logic (use payment-patterns)
project-specific: Decimal money handling, GDPR-aware logging (mask PII), Refugio domain enums
---
```

- [ ] **Step 3: Update rest-api-patterns.md**

Existing YAML frontmatter. Add `not-when`:

```yaml
---
name: rest-api-patterns
description: REST API design, request validation, versioning, error response standards, and pagination patterns
load-when: Designing API endpoint URLs, response envelopes, error schemas, or pagination for this project
not-when: FastAPI implementation details (use fastapi-patterns), database queries (use postgresql-patterns)
project-specific: Refugio error response envelope format, cursor-based pagination, EUR/PYG amount representation in JSON
---
```

- [ ] **Step 4: Update postgresql-patterns.md**

Existing YAML frontmatter. Add `not-when`:

```yaml
---
name: postgresql-patterns
description: PostgreSQL schema design, indexing strategy, migration patterns, query optimization, and common pitfalls
load-when: Schema design, writing migrations, Alembic, indexes, SQL queries, N+1 prevention FOR THIS PROJECT
not-when: FastAPI code, Python logic, payment processing — use domain-specific skills for those
project-specific: Refugio table naming, UUID PKs required, TIMESTAMPTZ always, animal status EXCLUDE constraint
---
```

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/fastapi-patterns.md .claude/skills/python-patterns.md \
        .claude/skills/rest-api-patterns.md .claude/skills/postgresql-patterns.md
git commit -m "docs: add not-when boundaries to generic tech skills"
```

---

## Task 6: Add Dispatch Contracts to Agent Definitions

**Problem**: Agents describe capabilities but not what they return or when to prefer them over inline work.

**Solution**: Add a `## Dispatch Contract` section to each agent with: trigger phrase, input, output format, and what stays in the main conversation.

- [ ] **Step 1: Add dispatch contract to ticket-manager.md**

Insert after the existing `## When to Use This Agent` section:

```markdown
## Dispatch Contract

**Trigger phrases**: "start ticket", "work on RAP-NNN", "update progress", "done", "finished", "switch to RAP-NNN"

**Input**: Ticket ID (RAP-NNN) + optional description for new tickets

**Output returned to main conversation**:
- For init: confirmation that tickets/RAP-NNN/ files created, list of files made
- For updates: updated context.md content (summary, not full file)
- For completion: validation results (pass/fail per level) + recap.md content

**Stays in agent**: File writing, progress log appending, timeline updates

**Do NOT dispatch for**: Reading a ticket to understand it (main agent can read directly)
```

- [ ] **Step 2: Add dispatch contract to schema-designer.md**

Insert after the `## Domain Context` section:

```markdown
## Dispatch Contract

**Trigger phrases**: "design the schema for", "create table for", "what's the schema for", "database design"

**Input**: Domain entity description (e.g., "design the animals and adopters tables")

**Output returned to main conversation**:
- Complete CREATE TABLE SQL statements ready to paste into an Alembic migration
- Index definitions with query-pattern rationale
- 3-5 bullet design decisions with reasoning

**Stays in agent**: Reading postgresql-patterns.md for conventions

**Do NOT dispatch for**: Writing the Alembic migration file itself (main agent does that), writing seed data
```

- [ ] **Step 3: Add dispatch contract to security-auditor.md**

Insert a `## Dispatch Contract` section:

```markdown
## Dispatch Contract

**Trigger phrases**: "security review", "audit this", "check for vulnerabilities", "GDPR review", "is this safe"

**Input**: File path(s) or code block to review

**Output returned to main conversation**:
- Severity-ranked finding list (CRITICAL / HIGH / MEDIUM / LOW)
- Each finding: file:line, what the vulnerability is, suggested fix
- GDPR-specific findings flagged separately
- Overall verdict: PASS / FAIL / NEEDS REVIEW

**Stays in agent**: Reading security rules and OWASP references

**Do NOT dispatch for**: Fixing the vulnerabilities (main agent implements fixes after review)
```

- [ ] **Step 4: Add dispatch contract to test-writer.md**

Insert a `## Dispatch Contract` section:

```markdown
## Dispatch Contract

**Trigger phrases**: "write tests for", "generate tests", "add test coverage", "test this module"

**Input**: File path to the module being tested + optional: which functions/classes to cover

**Output returned to main conversation**:
- Complete test file content, ready to write to tests/{layer}/test_{module}.py
- Coverage estimate for the generated tests
- List of edge cases covered

**Stays in agent**: Reading the source module, reading testing-patterns.md

**Do NOT dispatch for**: Running the tests (main agent runs pytest), fixing failing tests
```

- [ ] **Step 5: Add dispatch contract to doc-writer.md**

Insert a `## Dispatch Contract` section:

```markdown
## Dispatch Contract

**Trigger phrases**: "add docstrings to", "document this module", "generate API docs", "write docs for"

**Input**: File path(s) to document

**Output returned to main conversation**:
- Complete updated file content with docstrings added
- List of public functions documented

**Stays in agent**: Reading the source file

**Do NOT dispatch for**: Writing README.md (use /create-readme command), writing ADRs (use /adr command)
```

- [ ] **Step 6: Add dispatch contract to refactoring-advisor.md**

Insert a `## Dispatch Contract` section:

```markdown
## Dispatch Contract

**Trigger phrases**: "refactor", "analyze this code", "what should I clean up", "code smell", "technical debt"

**Input**: File path(s) to analyze

**Output returned to main conversation**:
- Prioritized list: HIGH / MEDIUM / LOW priority refactors
- Each item: what to change, why, estimated effort (lines affected)
- Which refactors are safe to do now vs. need tests first

**Stays in agent**: Reading the source files, reading clean-code.md

**Do NOT dispatch for**: Implementing the refactors (main agent does that based on the report)
```

- [ ] **Step 7: Commit**

```bash
git add .claude/agents/
git commit -m "docs: add dispatch contracts to all 6 agent definitions"
```

---

## Task 7: Update commands/README.md — Add Output Column

**Problem**: The README has Usage and Purpose but not what each command produces. When deciding between `/pre-commit-check` and `/code-review`, the output distinction matters.

**File:**
- Modify: `.claude/commands/README.md`

- [ ] **Step 1: Add Output column to each command table**

Update each table to add an `Output` column. Below are the values for each command:

**Ticket Workflow table**:

| Command | Usage | Output |
|---------|-------|--------|
| `/start-ticket` | `/start-ticket RAP-42 description` | Creates 5 ticket files in tickets/RAP-42/ + sets current.md |
| `/complete-ticket` | `/complete-ticket` | Validation report (4 levels) + recap.md created |
| `/update-progress` | `/update-progress` | Updated context.md + progress.md entry appended |
| `/switch-ticket` | `/switch-ticket RAP-56` | Pauses current ticket, resumes target ticket |
| `/execute-plan` | `/execute-plan [plan-file]` | Executes tasks step by step with checkpoints |

**Git & Release table**:

| Command | Usage | Output |
|---------|-------|--------|
| `/create-branch` | `/create-branch feature RAP-42 adoption-form` | New branch `feature/RAP-42-adoption-form` checked out |
| `/create-pr` | `/create-pr` | GitHub PR created, URL returned |
| `/changelog` | `/changelog` | CHANGELOG.md updated from git history |

**Code Quality table**:

| Command | Usage | Output |
|---------|-------|--------|
| `/pre-commit-check` | `/pre-commit-check` | Pass/fail per gate (lint, types, tests, security) |
| `/code-review` | `/code-review [file]` | Structured findings: severity, file:line, fix suggestion |
| `/refactor` | `/refactor [file]` | Prioritized refactor list (HIGH/MEDIUM/LOW) with effort |
| `/generate-missing-tests` | `/generate-missing-tests` | New test file(s) covering uncovered code |
| `/create-migration` | `/create-migration "description"` | Alembic migration file in migrations/ |

**Architecture table**:

| Command | Usage | Output |
|---------|-------|--------|
| `/adr` | `/adr "Use FastAPI over Django"` | New ADR file in docs/adr/ + README index updated |

**Project Documentation table**:

| Command | Usage | Output |
|---------|-------|--------|
| `/create-readme` | `/create-readme` | README.md written/updated from project structure |
| `/domain-spec` | `/domain-spec` | Markdown doc: domain objects, enums, business rules |
| `/catchup` | `/catchup [date or commit]` | Summary of changes since date/commit |

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/README.md
git commit -m "docs: add Output column to commands README"
```

---

## Self-Review

**Spec coverage check**:
1. ✅ Tech Stack locked — Task 1
2. ✅ Current Phase added — Task 1
3. ✅ Rules trimmed — Tasks 4a–4h (8 files)
4. ✅ Skill trigger boundaries — Task 5
5. ✅ ADR created — Task 2
6. ✅ First ticket created — Task 3
7. ✅ Agent dispatch contracts — Task 6
8. ✅ Commands README output column — Task 7

**Placeholder scan**: No TBDs in plan steps. All task steps have explicit content.

**Type consistency**: No code types — documentation only. No naming conflicts.

---

*Plan created: 2026-03-25*
*Estimated tasks: 7 (with sub-tasks 4a–4h = 14 discrete commits)*
