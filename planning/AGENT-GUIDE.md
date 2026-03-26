# Agent Work Guide — Refugio Animal Paraguay

This guide explains how agents claim and work on tasks to prevent work collisions and maintain smooth parallel development.

## Quick Start

1. Read `QUEUE.md` to see available tasks
2. Find a task with status 🟢 (ready)
3. Create a claim PR by running:
   ```bash
   git checkout -b claiming/TASK-123-agent-name
   # Add your claim to CLAIMING.md
   git add planning/CLAIMING.md
   git commit -m "chore: claim TASK-123"
   git push origin claiming/TASK-123-agent-name
   # Create PR
   ```
4. Once PR merges, the task is yours — begin implementation
5. When complete, update status to ✅ (done) in QUEUE.md

---

## Complete Workflow

### Phase 1: Read the Queue

Open `QUEUE.md` and understand the current state:

- 🟢 **ready** — No dependencies blocking. You can claim this.
- 🔒 **claimed** — Another agent claimed it. Wait or pick a different task.
- 🔨 **in_progress** — Agent is actively working. Do not touch.
- 👀 **review** — Waiting for code review. Do not touch.
- ✅ **done** — Completed. Move on.
- 🚧 **blocked** — Cannot start yet (dependencies). Do not claim.

### Phase 2: Understand the Task

Open the task file, e.g., `EPIC-0-testing-foundation/STORY-0.1-vitest-setup/TASK-0.1.1.md`:

Read the frontmatter:
```yaml
---
id: TASK-0.1.1
title: Set Up Vitest Configuration
epic: EPIC-0
story: STORY-0.1
priority: P0
status: ready
agent_type: fullstack
dependencies: []
branch: features/vitest-setup
claimed_by: null
claimed_at: null
pr_url: null
---
```

Read sections:
- **Description** — What needs to be built
- **Acceptance Criteria** — Specific requirements (checkboxes)
- **Technical Notes** — Architecture, patterns, libraries
- **Dependencies** — Tasks that must complete first

### Phase 3: Claim the Task

Create a feature branch with the claim:

```bash
# Navigate to project root
cd /home/ai-whisperers/Projects/refugio-animal-paraguay

# Create claiming branch
git checkout -b claiming/TASK-0.1.1-your-agent-name

# Edit CLAIMING.md and add your claim
cat >> planning/CLAIMING.md << 'EOF'
| TASK-0.1.1 | Set Up Vitest Configuration | your-agent-name | features/vitest-setup | $(date -u +%Y-%m-%dT%H:%M:%SZ) |
EOF

# Stage and commit
git add planning/CLAIMING.md
git commit -m "chore: claim TASK-0.1.1 - Vitest setup"

# Push
git push origin claiming/TASK-0.1.1-your-agent-name

# Create PR on GitHub
gh pr create \
  --title "CLAIM: TASK-0.1.1 - Vitest setup" \
  --body "Claiming task for implementation" \
  --base main \
  --draft
```

### Phase 4: Wait for Merge

The queue manager reviews and merges your claiming PR. Once merged:
- You have exclusive rights to the task
- Update the task's frontmatter to set `status: in_progress`
- Push your implementation branch

### Phase 5: Implement

Work on the implementation branch (e.g., `features/vitest-setup`):

```bash
# Switch to your feature branch
git checkout features/vitest-setup

# Make changes, commit as normal
git add src/
git commit -m "feat: configure vitest with defaults

- Add vitest.config.ts
- Configure paths alias
- Set coverage thresholds
- Add reporter options"

# When ready, update task status
# Edit TASK-0.1.1.md: status: review
git add planning/
git commit -m "chore: TASK-0.1.1 ready for review"

# Push
git push origin features/vitest-setup

# Create implementation PR
gh pr create \
  --title "TASK-0.1.1: Set Up Vitest Configuration" \
  --body "Implements vitest setup from acceptance criteria" \
  --base main \
  --reviewers "@lead-reviewer"
```

### Phase 6: Code Review & Merge

- Reviewer checks acceptance criteria against implementation
- Address feedback in follow-up commits
- Once approved, merge to main
- Update task status to ✅ (done) in QUEUE.md
- Delete feature branch

---

## Task File Format

Each task is a markdown file with YAML frontmatter. Example:

```yaml
---
id: TASK-0.1.1
title: Set Up Vitest Configuration
epic: EPIC-0
story: STORY-0.1
priority: P0
status: ready
agent_type: fullstack
dependencies: []
branch: features/vitest-setup
claimed_by: null
claimed_at: null
pr_url: null
---

## Description

Set up Vitest as the primary test framework with sensible defaults, including path alias resolution, coverage thresholds, and reporter configuration.

## Acceptance Criteria

- [ ] `vitest.config.ts` created with defaults
- [ ] Path alias `@/` resolves correctly in tests
- [ ] Coverage thresholds configured (80/75/95/90)
- [ ] HTML reporter configured
- [ ] `package.json` test scripts added
- [ ] `vitest` runs without error
- [ ] All checks pass

## Technical Notes

- Use Vitest v2.1.x (latest)
- Configure for ESM + TypeScript
- Include jsdom environment
- Set up @vitest/ui for debugging

## Dependencies

None — this is EPIC-0 start task.
```

---

## Priority Levels

Tasks are prioritized by phase. Work these in order:

### Phase 0: Foundation (EPIC-0)
**13 tasks** — All other work blocked until complete.
- Testing infrastructure
- Type checking setup
- Mock API setup
- Test coverage baseline

### Phase 1: Core Infrastructure (EPIC-8, EPIC-9)
**8 tasks** — Can start immediately after Phase 0.
- Database migrations
- Redis/BullMQ setup
- Design system
- Visual assets

### Phase 2: Features (EPIC-1, EPIC-3, EPIC-7)
**17 tasks** — Start after Phase 1 foundation.
- Animal catalog
- Lost & found
- PWA/offline
- i18n

### Phase 3: Advanced (EPIC-2, EPIC-5, EPIC-4, EPIC-6)
**28 tasks** — Last phase.
- Adoption workflow
- Admin panel
- Payments (multi-currency)
- User portal

---

## Conflict Prevention

### Rule 1: One Agent Per Task
A task can only be claimed by one agent. The claiming PR ensures atomicity.

### Rule 2: Claiming is Idempotent
Once a claiming PR merges, that agent has exclusive rights. Do not create duplicate claims.

### Rule 3: Block on Dependencies
If a task shows 🚧 (blocked), check `dependencies:` in the frontmatter. A prior task must complete first.

### Rule 4: Update Status Atomically
Each agent updates their task's `status:` field in the same commit where they update QUEUE.md. This prevents drift.

### Rule 5: PR Links Are Canonical
The `pr_url:` field in the task frontmatter is the single source of truth. If missing, work is not tracked.

---

## State Machine

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🟢 ready ──(claim PR)──> 🔒 claimed                   │
│     ▲                         │                         │
│     │                         │                         │
│     │                    (start working)               │
│     │                         │                         │
│     │                         ▼                         │
│     │                    🔨 in_progress                │
│     │                         │                         │
│     │                         │                         │
│     │                    (finish & test)               │
│     │                         │                         │
│     │                         ▼                         │
│     │                    👀 review                      │
│     │                         │                         │
│     │    (approved)      (needs work)                   │
│     │        │                │                         │
│     │        ▼                ▼                         │
│     │       ✅ done         🟢 ready (back)            │
│     │                         │                         │
│     └─────────────────────────┘                         │
│                                                         │
│  Any state ──(blocker found)──> 🚧 blocked            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Transitions

| From | To | Trigger | Who |
|------|----|---------|----|
| ready | claimed | Claiming PR merges | Agent |
| claimed | in_progress | Agent creates feature branch | Agent |
| in_progress | review | Agent creates implementation PR | Agent |
| review | done | PR approved & merged | Reviewer |
| review | ready | Changes requested | Reviewer |
| (any) | blocked | Dependency fails | Lead |

---

## Agent Types & Skills Mapping

### fullstack
- Next.js / React components
- Database schemas / migrations
- API endpoints
- Type definitions
- Tests (unit + integration)

**Recommended for**: Feature work, EPIC-1-4, EPIC-6

### devops
- Docker, Kubernetes, Terraform
- CI/CD pipeline
- Environment setup
- Infrastructure monitoring
- Secrets management

**Recommended for**: EPIC-8 infrastructure

### design
- Visual assets
- Design tokens
- UI/UX mockups
- Accessibility review
- Brand compliance

**Recommended for**: EPIC-9

### qa
- Test strategy
- Coverage analysis
- Performance testing
- Security scanning
- Release validation

**Recommended for**: EPIC-0 (all testing work)

---

## Troubleshooting

### "Task shows 🚧 blocked — what do I do?"

Check the `dependencies:` field in the task file. Example:

```yaml
dependencies:
  - TASK-0.1.1  # Vitest setup must complete first
  - TASK-0.1.2  # Type checking must be ready
```

Wait for those tasks to show ✅ (done), then the queue manager will unblock this task.

### "I claimed a task but can't find my branch"

The claiming PR only adds you to `CLAIMING.md`. You still need to:

1. Create your feature branch:
   ```bash
   git checkout -b features/your-task-name
   ```

2. Update the task's `branch:` field with the actual branch name

3. Push and create implementation PR

### "Two agents claimed the same task — conflict!"

The claiming PR system prevents this. If it happens anyway:

1. First PR merged wins — that agent owns the task
2. Second agent should abandon their claim
3. Queue manager resolves and picks next available task

### "Dependency task is taking too long"

Contact the lead or queue manager. They can:
- Reassign the blocking task to a faster agent
- Break it into smaller pieces
- Provide architectural guidance to unblock you

### "I found a bug in someone else's completed task"

Create an issue:

```bash
gh issue create \
  --title "BUG: TASK-X.X.X — [description]" \
  --label bug,dependencies \
  --body "This task has a regression that blocks downstream work"
```

The original agent or a new agent claims the fix.

---

## Conventions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org):

```
<type>(<scope>): <subject>

<body>

Closes #<issue-number>
TASK-X.X.X
```

Example:
```
feat(testing): add vitest configuration

- Add vitest.config.ts with path aliases
- Configure coverage thresholds
- Add HTML reporter

Closes #42
TASK-0.1.1
```

### Branch Names

Format: `<type>/<short-description>`

- `features/vitest-setup` — Feature work
- `claiming/TASK-0.1.1-agent-name` — Claiming branch
- `bugfix/animal-filter-crash` — Bug fix
- `docs/readme-update` — Documentation

### PR Titles

Include task ID and title:

```
TASK-0.1.1: Set Up Vitest Configuration

or

CLAIM: TASK-0.1.1 - Vitest setup
```

---

## Resources

- **QUEUE.md** — Current task status and availability
- **CLAIMING.md** — Who claimed what and when
- **Epic folders** — `EPIC-X-title/` directories with story & task files
- **Tech stack** — Next.js 14+, PostgreSQL, Prisma, Vitest, Playwright
- **Git repo** — `/home/ai-whisperers/Projects/refugio-animal-paraguay`

---

**Last updated**: 2026-03-25  
**Maintained by**: Refugio Animal Paraguay Team
