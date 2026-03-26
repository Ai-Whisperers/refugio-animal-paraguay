# Command: /create-branch
**Usage**: `/create-branch [type] [TICKET-ID] [description]`
**Example**: `/create-branch feature RAP-42 adoption-request-form`

---

## What This Does

Creates a properly named git branch following the project's branching strategy. Validates the branch type, ticket ID, and description before creating.

**Rules applied**: `.claude/rules/git-workflow.md`

---

## Branch Types

| Type | Use when | Branches from |
|------|---------|--------------|
| `feature` | New functionality | `develop` |
| `fix` | Bug fix | `develop` |
| `hotfix` | Critical production fix | `main` |
| `release` | Release preparation | `develop` |

---

## Workflow

### Step 1: Parse and Validate Input

From arguments:
- `$TYPE`: one of `feature`, `fix`, `hotfix`, `release`
- `$TICKET_ID`: format `RAP-NNN` (or `NNNN`)
- `$DESCRIPTION`: lowercase, hyphenated, 3-5 words

**Validate**:

```bash
# Validate ticket ID format
if [[ ! "$TICKET_ID" =~ ^RAP-[0-9]+$ ]]; then
  echo "❌ Invalid ticket ID format. Expected: RAP-NNN (e.g., RAP-42)"
  exit 1
fi

# Validate description (no spaces, no special chars except hyphens)
if [[ "$DESCRIPTION" =~ [^a-z0-9-] ]]; then
  echo "❌ Description must be lowercase with hyphens only"
  echo "   Got: $DESCRIPTION"
  echo "   Expected: adoption-request-form"
  exit 1
fi
```

If any argument is missing, ask for it.

### Step 2: Construct Branch Name

```
$TYPE/$TICKET_ID-$DESCRIPTION
```

Examples:
- `feature/RAP-42-adoption-request-form`
- `fix/RAP-67-donor-email-validation`
- `hotfix/RAP-91-payment-gateway-timeout`

Show the branch name and ask for confirmation if it looks long or unusual.

### Step 3: Determine Source Branch

```
feature → develop
fix     → develop
hotfix  → main
release → develop
```

```bash
git checkout $SOURCE_BRANCH
git pull origin $SOURCE_BRANCH
```

Warn if local source branch is behind remote by >5 commits.

### Step 4: Create Branch

```bash
git checkout -b $BRANCH_NAME
```

### Step 5: Confirm

```
✅ Branch created: $BRANCH_NAME
   Source: $SOURCE_BRANCH (up to date)
   Ready to work on $TICKET_ID

Next: Start working on $TICKET_ID
      /start-ticket $TICKET_ID [description] if ticket docs not yet created
```

---

## Branch Naming Quick Reference

```
feature/RAP-42-adoption-request-form   ✅
fix/RAP-67-donor-email-validation      ✅
hotfix/RAP-91-payment-timeout          ✅
release/1.2                            ✅

my-branch                              ❌ (no type, no ticket)
feature/RAP42                          ❌ (no hyphen in ticket)
feature/RAP-42-this-name-is-way-too-long ❌ (too long)
Feature/RAP-42-something               ❌ (capital F)
```

---

## FINAL MUST-PASS CHECKLIST

- [ ] Branch type is valid (feature/fix/hotfix/release)
- [ ] Ticket ID present and valid (RAP-NNN format)
- [ ] Description is lowercase and hyphenated
- [ ] Branch name ≤50 characters total
- [ ] Source branch is up-to-date before branching
- [ ] Branch successfully created locally
