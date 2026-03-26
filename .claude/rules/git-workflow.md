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
❌ my-branch
❌ fix-stuff
❌ feature/new_feature      (underscores)
❌ feature/RAP42            (missing hyphen)
❌ Feature/RAP-42-thing     (capital F)
❌ feature/RAP-42-this-is-way-too-long-a-name
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
- **Specific**: Describe what changed, not what you did ("Add donor validation" not "Work on donations")
- **50 chars** for subject line (80 max)
- **Body**: Use when explaining why (non-obvious decisions, tradeoffs)

### Examples
```
RAP-42: Add adoption request submission form

RAP-67: Fix email validation for international donors

Donors from EU countries were failing the old regex.
Updated to use a standards-compliant pattern that handles
all valid international email formats.

RAP-91: Update payment gateway timeout from 10s to 30s

Closes #91
```

### Anti-patterns
```
❌ fix bug
❌ wip
❌ updated stuff
❌ RAP-42 - changed form
❌ Add adoption request submission form (missing ticket ID)
```

---

## Branch Lifecycle

### Feature/Fix Flow

```
1. Branch from develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/RAP-42-adoption-form

2. Work on branch
   - Commit frequently with proper messages
   - Keep branch updated with develop (rebase or merge)

3. Before PR: pre-commit validation
   - Run /pre-commit-check
   - All quality gates must pass

4. Open PR: feature/RAP-42 → develop
   - PR title: "RAP-42: Add adoption request form"
   - Link ticket in description
   - Self-review diff before requesting review

5. After review: merge to develop
   - Squash or rebase merge (no merge commits unless needed)
   - Delete branch after merge

6. develop → release/x.y → main
   - Via release branch
   - Tag on main after merge
```

### Hotfix Flow

```
1. Branch from main
   git checkout main
   git checkout -b hotfix/RAP-91-payment-timeout

2. Fix, test, validate

3. PR: hotfix/RAP-91 → main
   Simultaneously: cherry-pick or merge to develop

4. Tag release on main
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

## Notes (optional)
Any reviewer guidance, known issues, or follow-up tickets.
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

`main` and `develop` are protected:
- Direct commits forbidden
- Require PR with at least 1 review
- All CI/CD checks must pass
- No force pushes

---

## Tag Strategy

For releases:
```
v1.0.0       ← Production release
v1.0.0-rc.1  ← Release candidate
v1.0.0-beta  ← Beta testing
```

Tag after merging release branch to main:
```bash
git tag -a v1.2.0 -m "Release v1.2.0: [summary]"
git push origin v1.2.0
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
