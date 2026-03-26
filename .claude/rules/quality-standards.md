# Rule: Quality Standards
**ID**: rule.quality.standards.v1
**Version**: 1.0.0
**Applies to**: All code and validation in this repository

---

## Zero Warnings, Zero Errors Standard

### Quality Gates (ALL must pass before commit)

| Gate | What it checks | Tool |
|------|---------------|------|
| **Build/Compile** | No compilation errors, all imports resolve | Language compiler/bundler |
| **Linting** | Style violations, unused vars, bad patterns | ESLint / Pylint / Ruff |
| **Type Checking** | Type mismatches, missing annotations | TypeScript / mypy |
| **Tests** | All tests pass, no unexpected skips | pytest / jest / vitest |
| **Format** | Consistent formatting | Prettier / Black |
| **Security** | No secrets in code, no vulnerable deps | Bandit / npm audit / gitleaks |

### Pre-Commit Validation Workflow

```
1. Make code changes
2. Run validation: check each gate above
3. Review ALL warnings and errors
4. Fix all issues (see: When to suppress vs fix)
5. Re-run validation — confirm clean
6. Commit ONLY after clean pass
```

**Fast feedback** — validation should take <60 seconds. If slow, optimize.

---

## Diagnostic Message Standards

Every error message, validation failure, and warning must follow the **WHAT + WHY + HOW** structure.

### Structure

```
🔴 ERROR: [WHAT — precise description of what is wrong]
   Why:   [WHY — why this is a problem, what impact it has]
   Fix:   [HOW — exact steps to resolve, specific not generic]
   Where: [file:line if applicable]
   Help:  [command or doc link if available]
```

### Severity Levels

**🔴 ERROR (Blocker)**
- Prevents build, test, or deployment
- Must fix before commit — no exceptions
- Required fields: WHAT + WHY + HOW + WHERE + EXAMPLE

**🟡 WARNING (Should fix)**
- Code runs but violates standards
- Must fix before commit (zero-tolerance)
- Required fields: WHAT + IMPACT + HOW + WHERE

**🔵 INFO (FYI)**
- Helpful context, not a problem
- Optional to act on
- Required fields: WHAT + CONTEXT

### Good vs Bad Diagnostic Examples

```
❌ BAD: "Error: validation failed"
   - No WHAT: What validation? What failed?
   - No WHY: Why is this an error?
   - No HOW: What do I do?

✅ GOOD:
🔴 ERROR: Donor email format invalid
   Why:   EU donor API requires RFC 5322 compliant emails — non-standard
           addresses will silently fail during payment processing.
   Fix:   Validate with: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
           or use the existing validateDonorEmail() utility in src/utils/validation.ts
   Where: src/components/DonorForm.tsx:47
   Help:  /pre-commit-check to re-validate after fix
```

```
❌ BAD: "Test failed"

✅ GOOD:
🔴 ERROR: Unit test failure — AdoptionService.submitRequest()
   Why:   AdoptionService.submitRequest() throws when adopter has pending
           applications — this would crash the adoption form for returning users.
   Fix:   1. Open tests/adoption.test.ts:83
           2. Check that the mock returns pendingCount: 0 by default
           3. The test expects an error for valid input — update assertion
   Where: tests/adoption.test.ts:83
```

---

## Tool-Specific Validation Commands

### Python Projects
```bash
# Full validation sequence
ruff check .              # Linting (fast)
mypy src/                 # Type checking
black --check .           # Format check
pytest --tb=short         # Tests
bandit -r src/            # Security scan
```

### Node.js/TypeScript Projects
```bash
# Full validation sequence
npm run lint              # ESLint
npm run type-check        # TypeScript
npm run format:check      # Prettier
npm test                  # Jest/Vitest
npm audit                 # Dependency security
```

### Common pre-commit script pattern (Python)
```python
#!/usr/bin/env python3
"""Pre-commit validation script."""
import subprocess
import sys

checks = [
    (["ruff", "check", "."], "Linting"),
    (["mypy", "src/"], "Type checking"),
    (["black", "--check", "."], "Formatting"),
    (["pytest", "--tb=short", "-q"], "Tests"),
]

failed = []
for cmd, name in checks:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"🔴 {name} FAILED:")
        print(result.stdout)
        print(result.stderr)
        failed.append(name)
    else:
        print(f"✅ {name} passed")

if failed:
    print(f"\n❌ {len(failed)} check(s) failed: {', '.join(failed)}")
    print("Fix all issues before committing.")
    sys.exit(1)
else:
    print("\n✅ All checks passed — ready to commit")
```

---

## Code Coverage

- **Target**: 80% line coverage for new code
- **Never decrease** overall coverage with a PR
- **Critical paths** (payment, auth, data integrity): 95%+
- Coverage reports must be reviewed in PR, not just passing/failing

```bash
# Python
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Node.js
jest --coverage --coverageThreshold='{"global":{"lines":80}}'
```

---

## Security Standards

- **No secrets in code**: Use environment variables
- **Dependency auditing**: `pip-audit` or `npm audit` — fail on high/critical
- **Input validation**: Validate all user input at system boundaries
- **SQL safety**: Parameterized queries only — no string concatenation
- **Auth**: Every API endpoint must declare its auth requirement

```python
# ❌ NEVER
query = f"SELECT * FROM animals WHERE name = '{user_input}'"

# ✅ ALWAYS
query = "SELECT * FROM animals WHERE name = %s"
cursor.execute(query, (user_input,))
```

---

## FINAL MUST-PASS CHECKLIST

Before every commit:
- [ ] Zero errors (build, lint, type check, tests)
- [ ] Zero warnings (or each has a specific justification comment)
- [ ] All tests pass — no skips without justification
- [ ] No hardcoded credentials or secrets
- [ ] No `TODO` or `FIXME` that belong to this ticket
- [ ] Coverage not decreased below threshold
- [ ] Security scan clean
- [ ] Diagnostic messages follow WHAT+WHY+HOW format
