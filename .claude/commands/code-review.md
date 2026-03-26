---
name: code-review
description: Full code review against Refugio quality, security, and domain standards
allowed-tools: Read, Grep, Bash
---

@.claude/rules/quality-standards.md
@.claude/rules/clean-code.md

# Command: /code-review
**Usage**: `/code-review [file or PR]`
**Example**: `/code-review src/services/AdoptionService.py`
**Example**: `/code-review` (reviews all staged/changed files via `git diff develop`)

---

## What This Does

Performs a structured code review against project standards. Reviews for correctness, quality, security, and maintainability. Provides structured feedback with specific fixes.

**Rules applied**: `.claude/rules/clean-code.md`, `.claude/rules/quality-standards.md`

---

## Review Criteria

Review each changed file against these categories:

### Category 1: Correctness
- Does the code do what it's supposed to do?
- Are edge cases handled (null, empty, error states)?
- Are there potential runtime errors?
- Is input validated at system boundaries?

### Category 2: Clean Code
- **Names**: Do they reveal intent? No generic names (data, temp, result)?
- **Functions**: Single responsibility? Not too long (>30 lines = suspicious)?
- **DRY**: Is logic duplicated from elsewhere in the file or project?
- **Constants**: Named constants or magic values?
- **Comments**: Do comments explain "why" not "what"?
- **Error handling**: Specific exception types? No silent swallowing?

### Category 3: Type Safety
- Are all function signatures typed?
- Are nullable values handled with null checks?
- Are domain types used (e.g., `DonorId` not `int`)?

### Category 4: Security
- No hardcoded credentials
- User inputs validated/sanitized
- SQL queries parameterized
- No sensitive data in logs
- GDPR considerations for EU donor data

### Category 5: Tests
- Is new code covered by tests?
- Are tests testing behavior, not implementation?
- Do test names describe the scenario?

### Category 6: Performance
- No O(n²) patterns where O(n) is possible
- No repeated DB queries in loops (N+1 problem)
- Heavy operations async where appropriate

---

## Workflow

### Step 1: Identify Files to Review

```bash
git diff --name-only HEAD
# or use the provided file argument
```

### Step 2: Read Each File

Read each changed file completely before commenting.

### Step 3: Review Against All 6 Categories

For each finding, format as:

```
[file:line] [severity]
Issue: [What is wrong — specific and precise]
Why:   [Why this matters — risk, impact]
Fix:   [How to fix — specific, not generic]

Example (fix included):
  # Before
  result = process_data(data)

  # After
  adoption_record = build_adoption_record(adopter_data)
```

**Severity levels**:
- 🔴 **Must fix**: Correctness error, security issue, test failure
- 🟡 **Should fix**: Standards violation, maintainability issue
- 🔵 **Consider**: Non-blocking suggestion, alternative approach

### Step 4: Overall Assessment

```
## Review Summary

**Overall**: ✅ Approved / ⚠️ Approve with minor changes / ❌ Changes requested

**Breakdown**:
- Correctness: ✅ No issues
- Clean code: ⚠️ 2 naming issues, 1 function too long
- Type safety: ✅ All typed
- Security: ✅ No issues
- Tests: ⚠️ Missing test for error case
- Performance: ✅ No issues

**Must fix (1)**:
  [List 🔴 items]

**Should fix (3)**:
  [List 🟡 items]

**Consider (2)**:
  [List 🔵 items]
```

---

## Example Review Feedback

### Good feedback (specific + fix included)

```
src/services/DonationService.py:47 🟡
Issue: Magic number 30 used directly — intent unclear
Why:   In 3 months, no one will know why 30 was chosen
Fix:   Add constant at top of file:
       PAYMENT_RETRY_DAYS = 30
       Then use: if days_since_attempt > PAYMENT_RETRY_DAYS:
```

```
src/services/DonationService.py:89-134 🟡
Issue: processDonation() does 4 things — validate, charge, record, notify
Why:   Single responsibility violation — hard to test and debug independently
Fix:   Extract to:
       validate_donation_request(donor, amount) → None (raises on invalid)
       charge_payment_gateway(donor, amount) → PaymentResult
       record_donation(donor, amount, payment_result) → DonationRecord
       notify_donation_received(donor, donation_record) → None
```

```
src/api/adoption_routes.py:23 🔴
Issue: SQL query uses string interpolation with user input
Why:   SQL injection vulnerability — an attacker can destroy the database
Fix:   Use parameterized query:
       # Before (VULNERABLE):
       cursor.execute(f"SELECT * FROM animals WHERE name = '{name}'")
       # After (SAFE):
       cursor.execute("SELECT * FROM animals WHERE name = %s", (name,))
```

### Bad feedback (avoid)

```
❌ "This code could be improved"
❌ "Consider refactoring this section"
❌ "The naming here is not ideal"
```

These are useless without specifics. Always include: which line, what's wrong, how to fix.

---

## Refugio Animal Paraguay — Domain-Specific Checklist

In addition to general review criteria, check for:

- [ ] Donor data handling: GDPR consent checked before EU donor marketing
- [ ] Currency handling: EUR/PYG conversions use approved exchange rate service
- [ ] Animal records: Status transitions validated (can't adopt an animal already adopted)
- [ ] Auth: Volunteer/adopter/staff/admin permissions checked at API layer
- [ ] Donations: Payment failures logged with full context (never fail silently)
- [ ] Email: Sensitive donor info not included in logs or error messages

---

## FINAL MUST-PASS CHECKLIST

- [ ] All 6 categories reviewed for each file
- [ ] All 🔴 must-fix items called out clearly
- [ ] Each issue has: location (file:line), issue, why, fix
- [ ] Fix suggestions are specific (code example where helpful)
- [ ] Domain-specific security checks done
- [ ] Overall assessment provided
- [ ] No nitpicking formatting if linter handles it
- [ ] No suggesting changes to code not in scope of the PR
