# Autonomous Claude Code Development — Research & Recommendations

**Date**: 2026-03-26
**Context**: Deep research into community practices, frameworks, and patterns for running Claude Code autonomously on the Refugio Animal Paraguay project.

---

## Executive Summary

The Claude Code community has developed several mature patterns for autonomous, around-the-clock development. The key findings center on three areas: scheduling infrastructure, quality enforcement, and self-improvement loops. Below are the most actionable frameworks discovered, followed by specific recommendations for our project.

---

## 1. Scheduling Infrastructure

### Desktop vs Cloud vs /loop

| Feature | Desktop Scheduled Tasks | Cloud Scheduled Tasks | /loop |
|---------|------------------------|----------------------|-------|
| Runs when machine is off | No | Yes | No |
| Survives app restart | Yes | Yes | No |
| Max duration | Session-based | Session-based | 3-day expiry |
| Git worktree isolation | Supported | Supported | No |
| Best for | Dev machines that stay on | True 24/7 coverage | Short iterative loops |

**Key finding**: Desktop tasks only run while the machine is awake and Claude Desktop is open. For true 24/7, Cloud scheduled tasks are the path forward — they run on Anthropic's infrastructure regardless of local machine state.

### Worktree Isolation

Scheduled tasks support `isolation: "worktree"` which creates a temporary git worktree for each run. This prevents conflicts between:
- Manual work in the main checkout
- Multiple scheduled runs overlapping
- Branch state corruption from concurrent git operations

**Recommendation**: Enable worktree isolation on all scheduled tasks.

---

## 2. Community Frameworks

### metaswarm (GitHub: lspecian/metaswarm)

The most comprehensive autonomous framework found. Key architecture:

- **18 specialized agents** with role-based dispatch (architect, implementer, tester, reviewer, etc.)
- **9-phase workflow**: Discovery → Planning → Implementation → Testing → Review → Documentation → Integration → Deployment → Monitoring
- **Blocking quality gates** between phases — not advisory, the pipeline stops
- **Self-improving knowledge base** (JSONL format): agents log learnings after each task, which feed into future planning
- **Consensus mechanism**: Multiple agents vote on architectural decisions before implementation

**What we can adopt**:
- The JSONL learning log pattern — after each story completion, append what worked and what didn't
- Blocking quality gates (we already have `make all-checks`, but should enforce it in the scheduled task prompt)
- Phase-based workflow aligns well with our existing ticket system

### Ralph Orchestrator (GitHub: dirkjot/ralph-orchestrator)

Focused on continuous execution with human oversight:

- **Infinite loop with backpressure**: Runs continuously until `LOOP_COMPLETE` signal, but has iteration caps and cooldown periods
- **Human escalation via Telegram**: When stuck after N retries, sends a message asking for help rather than looping forever
- **State persistence**: Writes orchestrator state to disk so it can resume after crashes
- **Quality gate enforcement**: Each iteration must pass gates before the next begins

**What we can adopt**:
- Iteration caps — our scheduled tasks should have a max-attempts counter (3 attempts, then log blocker and move on)
- The state persistence pattern — our `tickets/RAP-NNN/context.md` RESUME_POINT already supports this
- Backpressure — if a story fails quality gates 3 times, mark BLOCKED and pick next READY story

### claude-code-scheduler (GitHub: anthropics/claude-code-scheduler)

Official-adjacent tool for OS-level cron scheduling:

- Uses system crontab directly rather than Claude Desktop scheduling
- Worktree isolation built-in
- Structured logging per run
- Supports both one-shot and recurring patterns

**What we can adopt**:
- OS-level cron as a fallback if Desktop scheduling proves unreliable
- The structured logging pattern for our `planning/orchestrator-log.md`

### awesome-claude-code (GitHub: anthropics/awesome-claude-code)

Curated index of autonomous tools and patterns. Notable entries beyond the above:

- **ruflo**: Swarm orchestration for parallel agent dispatch
- **claude-code-power-pack**: Hook collection for quality enforcement
- **tts-notify**: Audio notifications when tasks complete (we already have this via our stop hook)
- **CLAUDE.md generators**: Tools that auto-generate project instructions from codebase analysis

---

## 3. Quality Enforcement Patterns

### The Gate Pattern (from metaswarm)

```
[Implement] → GATE(lint) → GATE(type-check) → GATE(test) → GATE(security) → [Commit]
```

Each gate is **blocking** — failure means the pipeline stops and the agent must fix the issue before proceeding. This differs from advisory checks where failures are logged but don't block.

Our current setup has `make all-checks` but the scheduled task prompt should explicitly enforce:
1. Run gate
2. If fail → fix → re-run (max 3 attempts)
3. If still failing → log blocker, mark story BLOCKED, move to next READY story

### Coverage Ratchet

Never allow coverage to decrease. Each PR must maintain or improve the coverage percentage. This prevents the common pattern where autonomous agents write code without adequate tests.

We already enforce `--cov-fail-under=80` — this is correct.

### Commit Frequency

Community consensus: commit after every logical unit of work, not just at the end. Benefits:
- Easier to bisect failures
- Progress is visible even if a run gets interrupted
- Smaller diffs are easier to review

Our CLAUDE.md already mandates this. The scheduled task prompts should reinforce it.

---

## 4. Self-Improvement Patterns

### JSONL Learning Log (from metaswarm)

After each completed story, append a structured entry:

```jsonl
{"date": "2026-03-26", "ticket": "RAP-013", "story": "CORS + Rate Limiting", "duration_est": "5pts", "actual_duration": "~3h", "blockers": ["none"], "learnings": ["FastAPI CORSMiddleware order matters - must be added before route registration"], "quality_gates_passed": true}
```

Over time, this builds a searchable knowledge base that informs future planning and estimation.

**Recommendation**: Create `planning/learnings.jsonl` and append after each story completion.

### Pattern Library

When an agent discovers a useful pattern (e.g., "how to test async FastAPI endpoints with real DB"), it writes it to a shared patterns directory. Future agents read these before starting related work.

We already have `.claude/skills/` for this — our scheduled tasks should be prompted to update skill files when they discover new patterns.

---

## 5. Specific Recommendations for Refugio

### Immediate Actions

1. **Enable worktree isolation** on both scheduled tasks — prevents git conflicts between manual and automated work

2. **Add iteration caps** to the scheduled task prompts — max 3 fix attempts per quality gate, then mark BLOCKED and move on

3. **Create `planning/learnings.jsonl`** — append structured learnings after each story completion

4. **Run scheduled tasks manually once** to pre-approve tool permissions — both `refugio-autonomous-worker` and `refugio-work-checker` need initial manual trigger

5. **Add `unset GITHUB_TOKEN`** to scheduled task environment setup — prevents stale token interference (already in current prompts)

### Medium-Term Improvements

6. **Migrate to Cloud scheduled tasks** when available — ensures work continues even when the machine sleeps or restarts

7. **Add Telegram/webhook notification** for blocker escalation — when a story is marked BLOCKED after 3 attempts, notify Ivan

8. **Implement learning extraction** — after each story, the agent appends to `planning/learnings.jsonl` with what worked and what didn't

9. **Quality gate dashboard** — a simple script that reads orchestrator-log.md and learnings.jsonl to show pass/fail rates, average story duration, common blocker patterns

### Architecture Alignment

Our existing setup already covers many best practices:
- Ticket system with structured state (`tickets/RAP-NNN/`) aligns with metaswarm's phase tracking
- Quality gates via `make all-checks` align with the gate pattern
- RESUME_POINT in context.md aligns with Ralph's state persistence
- Commit-per-logical-unit policy aligns with community consensus
- Skills directory aligns with the pattern library concept

The main gaps are: worktree isolation, iteration caps, learning extraction, and Cloud scheduling for true 24/7.

---

## Sources

- [Claude Code Official Docs — Scheduled Tasks](https://docs.claude.com) — Desktop vs Cloud vs /loop comparison
- [metaswarm](https://github.com/lspecian/metaswarm) — 18-agent autonomous framework with quality gates
- [ralph-orchestrator](https://github.com/dirkjot/ralph-orchestrator) — Continuous loop with backpressure and human escalation
- [awesome-claude-code](https://github.com/anthropics/awesome-claude-code) — Curated index of autonomous tools
- [claude-code-scheduler](https://github.com/anthropics/claude-code-scheduler) — OS-level cron scheduling

---

*Generated from deep research conducted 2026-03-26*
