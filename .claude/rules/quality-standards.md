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

---

## Diagnostic Message Standards

Every error message must follow the **WHAT + WHY + HOW** structure.

### Structure

```
🔴 ERROR: [WHAT — precise description of what is wrong]
   Why:   [WHY — why this is a problem, what impact it has]
   Fix:   [HOW — exact steps to resolve, specific not generic]
   Where: [file:line if applicable]
   Help:  [command or doc link if available]
```

### Severity Levels

| Level | When | Required fields |
|-------|------|----------------|
| **🔴 ERROR** | Prevents build/test/deploy | WHAT + WHY + HOW + WHERE |
| **🟡 WARNING** | Violates standards, code still runs | WHAT + IMPACT + HOW + WHERE |
| **🔵 INFO** | Helpful context, not a problem | WHAT + CONTEXT |

### Example

```
✅ GOOD:
🔴 ERROR: Donor email format invalid
   Why:   EU donor API requires RFC 5322 compliant emails — non-standard
           addresses will silently fail during payment processing.
   Fix:   Validate with: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
           or use the existing validateDonorEmail() utility in src/utils/validation.ts
   Where: src/components/DonorForm.tsx:47
   Help:  /pre-commit-check to re-validate after fix

❌ BAD: "Error: validation failed"
   (No WHAT, no WHY, no HOW)
```

---

## Validation Commands (Python)

```bash
ruff check .              # Linting (fast)
mypy src/                 # Type checking
black --check .           # Format check
pytest --tb=short         # Tests
bandit -r src/            # Security scan
```

---

## Code Coverage

- **Target**: 80% line coverage for new code
- **Never decrease** overall coverage with a PR
- **Critical paths** (payment, auth, data integrity): 95%+

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
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
