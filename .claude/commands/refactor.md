---
name: refactor
description: Analyze code for refactoring opportunities and produce a prioritized improvement plan
allowed-tools: Bash, Read, Glob, Grep
---

@.claude/rules/clean-code.md

Analyze code for refactoring opportunities. Produce a prioritized, actionable plan — do not make changes unless the user explicitly approves.

## Steps

**Step 1** — Identify target scope:
- If argument provided (e.g., `/refactor src/services/`), analyze that path
- Otherwise, analyze files changed in current ticket (from `git diff --name-only HEAD~1..HEAD`)

**Step 2** — Static analysis:
```bash
# Find long functions (>30 lines)
grep -n "def " <file> | head -30

# Find duplicated patterns
grep -rn "pattern" src/

# Type coverage check
mypy <file> --show-error-codes 2>&1 | head -30

# Complexity check (if radon available)
python3 -m radon cc <file> -a -nc 2>/dev/null || echo "radon not installed"
```

**Step 3** — Read and analyze flagged sections:
- Read files identified above
- Look for: magic values, duplicated logic, long functions, single-responsibility violations, mutable defaults, bare excepts

**Step 4** — Produce prioritized refactoring plan:

```markdown
## Refactoring Analysis — [file or scope]

### Priority 1 — Bug Risk (fix before next commit)
- [ ] Issue: [description]
  - File: path/to/file.py:line
  - Problem: [what's wrong and why it's risky]
  - Fix: [specific approach]

### Priority 2 — Clarity (fix this sprint)
- [ ] Issue: [description]
  - File: path/to/file.py:line
  - Problem: [what makes this hard to understand/change]
  - Fix: [specific approach]

### Priority 3 — Nice to Have (backlog)
- [ ] Issue: [description]
  - File: path/to/file.py:line
  - Fix: [specific approach]

### Metrics Summary
- Functions >30 lines: N
- Magic values found: N
- Duplicated logic blocks: N
- Missing type annotations: N
- Complexity rank D/E/F: N
```

## Rules

- Identify problems, do not fix unless asked
- Prioritize by risk: bugs > clarity > aesthetics
- Reference exact file:line for every finding
- Never include "refactor everything" — be specific
- If scope is clean, say so: "No high-priority refactoring needed"
