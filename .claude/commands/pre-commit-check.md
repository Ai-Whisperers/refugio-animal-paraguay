# Command: /pre-commit-check
**Usage**: `/pre-commit-check`
**Aliases**: `/validate`, `/check`

---

## What This Does

Runs all quality gates locally before committing. Mirrors the CI/CD pipeline so you don't discover failures after pushing. Reports all issues with structured WHAT+WHY+HOW diagnostics.

**Zero-tolerance policy**: All gates must pass. No partial passes.

**Rules applied**: `.claude/rules/quality-standards.md`

---

## Workflow

### Step 1: Check What's Changed

```bash
git diff --name-only HEAD
git diff --cached --name-only  # staged files
```

Identify changed file types to determine which gates to run.

### Step 2: Run All Quality Gates

Run gates appropriate to the project stack. Report results for each.

#### Python Stack

```bash
echo "=== Linting ==="
ruff check .
# or: flake8 . --max-line-length=120

echo "=== Type Checking ==="
mypy src/ --ignore-missing-imports

echo "=== Formatting ==="
black --check .
isort --check-only .

echo "=== Tests ==="
pytest --tb=short -q

echo "=== Coverage ==="
pytest --cov=src --cov-report=term-missing --cov-fail-under=80 -q

echo "=== Security ==="
bandit -r src/ -ll -q
pip-audit --disable-pip
```

#### Node.js/TypeScript Stack

```bash
echo "=== Linting ==="
npm run lint

echo "=== Type Checking ==="
npm run type-check  # or: npx tsc --noEmit

echo "=== Formatting ==="
npm run format:check  # or: npx prettier --check .

echo "=== Tests ==="
npm test -- --run  # or: npm test -- --watchAll=false

echo "=== Coverage ==="
npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'

echo "=== Security ==="
npm audit --audit-level=high
```

### Step 3: Report Results

For each gate:

```
✅ Linting: clean (0 warnings, 0 errors)
✅ Type check: clean (0 errors)
✅ Formatting: correct
✅ Tests: 47 passing, 0 failing, 0 skipped
✅ Coverage: 84.2% (threshold: 80%)
✅ Security: no vulnerabilities
```

Or if issues found:

```
🔴 Linting: 2 issues found

   🔴 ERROR: no-unused-vars
   Where: src/components/AdoptionForm.tsx:47
   What: Variable 'requestId' is declared but never read
   Why:  Unused variables bloat the bundle and cause confusion
   Fix:  Remove 'requestId' declaration, or prefix with _ if intentional: '_requestId'

   🟡 WARNING: prefer-const
   Where: src/services/donation.ts:89
   What: 'formData' is never reassigned — use 'const' instead of 'let'
   Why:  'const' signals immutability and prevents accidental reassignment
   Fix:  Change: let formData = ...
              To: const formData = ...
```

### Step 4: Final Summary

If ALL pass:
```
✅ All quality gates passed — safe to commit

Suggested commit:
  git commit -m "RAP-42: [brief description of what changed]"
```

If ANY fail:
```
❌ Pre-commit check failed — DO NOT commit yet

Gates failed:
  • Linting: 2 issues
  • Tests: 1 failing

Fix all issues above and run /pre-commit-check again.
```

---

## Diagnostic Message Format

Every issue reported must follow WHAT + WHY + HOW:

```
[severity icon] [Gate]: [brief issue title]
Where: [file:line if applicable]
What:  [Precise description of the problem]
Why:   [Why this is a problem — impact, risk]
Fix:   [Exact steps to resolve — specific, not "fix it"]
```

**Severity icons**:
- 🔴 ERROR — Must fix, blocks commit
- 🟡 WARNING — Must fix (zero-tolerance), blocks commit
- 🔵 INFO — Suggestion, doesn't block

---

## Common Issues and Fixes

### Linting

```
🟡 Unused import
Fix: Remove the import, or check if it's used elsewhere in the file first.
```

```
🟡 Magic number
Fix: Replace with a named constant at the top of the file.
Example: ADOPTION_TIMEOUT_DAYS = 30
```

### Type Errors

```
🔴 Object is possibly undefined
Fix: Add null check before accessing:
  if (animal && animal.status) { ... }
  or use optional chaining: animal?.status
```

```
🔴 Type 'string' is not assignable to type 'Currency'
Fix: Import the Currency type and cast:
  const currency: Currency = 'EUR'
  or add to the union: type Currency = 'EUR' | 'USD' | 'PYG'
```

### Tests

```
🔴 Test failure: expected 'AVAILABLE' but received 'PENDING'
Fix: Check if the test data or the service logic is wrong.
     Run the specific test to see full output:
     pytest tests/test_adoption.py::test_animal_status -v
```

### Coverage

```
🟡 Coverage below threshold: 74% (threshold: 80%)
Fix: Add tests for the uncovered lines listed above.
     Focus on: src/services/AdoptionService.py (lines 45-67)
     Run with: pytest --cov=src --cov-report=html
     Then open: htmlcov/index.html
```

---

## FINAL MUST-PASS CHECKLIST

- [ ] All linting checks pass (zero warnings/errors)
- [ ] All type checks pass (zero errors)
- [ ] All tests pass (zero failures, justified skips only)
- [ ] Coverage above threshold for this branch
- [ ] Security scan clean (no high/critical)
- [ ] No debug code (console.log, print, breakpoints)
- [ ] No hardcoded credentials or secrets
- [ ] Formatting consistent (or formatter run)
