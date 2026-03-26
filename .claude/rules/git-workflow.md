# Rule: Git Workflow
**ID**: rule.git.workflow.v1
**Version**: 1.0.0
**Applies to**: All git operations in this repository

---

## Branch Structure

```
main          ← Production-ready code only. Direct commits forbidden.
develop       ← Integration branch. All features merge here first.
feature/*     ← New functionality (branches from develop)
fix/*         ← Bug fixes (branches from develop)
hotfix/*      ← Critical production fixes (branches from main)
release/*     ← Release preparation (branches from develop)
```

## Branch Naming

### Pattern
```
[type]/[TICKET-ID]-[brief-description]
```

### Rules
- Type: `feature`, `fix`, `hotfix`, `release`
- Ticket ID: `RAP-NNN` (always required, links to ticket)
- Description: lowercase, hyphenated, 3-5 words maximum
- No special characters except hyphens

### Examples
```
feature/RAP-42-adoption-request-form
fix/RAP-67-donor-email-validation
hotfix/RAP-91-payment-gateway-timeout
release/1.2
```

### Anti-patterns
```
❌ my-branch                            (no ticket ID)
❌ feature/new_feature                  (underscores)
❌ Feature/RAP-42-this-is-way-too-long  (capital F, too long)
```

---

## Commit Message Standards

### Format
```
RAP-NNN: [imperative verb] [what changed]

[Optional body: why, context, breaking changes]

[Optional footer: Co-authored-by, Closes #NNN]
```

### Rules
- **Always** reference ticket ID
- **Imperative mood**: "Add", "Fix", "Update", "Remove" — not "Added", "Fixes", "Updates"
- **Specific**: Describe what changed, not what you did
- **50 chars** for subject line (80 max)
- **Body**: Use when explaining why (non-obvious decisions, tradeoffs)

### Examples
```
RAP-42: Add adoption request submission form

RAP-67: Fix email validation for international donors

Donors from EU countries were failing the old regex.
Updated to use a standards-compliant pattern.
```

### Anti-patterns
```
❌ fix bug
❌ Add adoption request submission form  (missing ticket ID)
```

---

## Pull Request Standards

### Title Format
```
RAP-NNN: [Brief description matching commit subject]
```

### Required PR Body
```markdown
## Summary
- What this PR does (2-3 bullets)

## Ticket
RAP-NNN: [Link or description]

## Changes
- File 1: What changed and why
- File 2: What changed and why

## Test Plan
- [ ] Tested locally
- [ ] Unit tests pass
- [ ] Manual test: [describe scenario]
```

### Definition of Done (PR checklist)
- [ ] All acceptance criteria from ticket met
- [ ] Zero linting warnings/errors
- [ ] Zero type errors
- [ ] All tests pass (no skips)
- [ ] New code has appropriate tests
- [ ] No hardcoded credentials or debug code
- [ ] PR description complete

---

## Protected Branches

`main` and `develop`: direct commits forbidden, require PR + 1 review, all CI checks must pass, no force pushes.

---

## Tag Strategy

```
v1.0.0       ← Production release
v1.0.0-rc.1  ← Release candidate
v1.0.0-beta  ← Beta testing
```

---

## FINAL MUST-PASS CHECKLIST

Before creating a branch:
- [ ] Branch type is correct (feature/fix/hotfix/release)
- [ ] Ticket ID present and valid (RAP-NNN)
- [ ] Description is lowercase hyphenated, ≤5 words

Before committing:
- [ ] Commit message references ticket ID
- [ ] Imperative mood in subject
- [ ] Subject ≤50 characters (80 max)
- [ ] Pre-commit validation passes (zero warnings/errors)

Before opening PR:
- [ ] All acceptance criteria met
- [ ] Quality gates pass
- [ ] PR body complete
- [ ] Self-reviewed diff
