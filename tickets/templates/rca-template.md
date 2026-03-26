# TICKET-ID Root Cause Analysis

_Create this file only for defect tickets — bugs, regressions, security incidents._

---

## Problem Statement

**What broke**: [Precise description of the failure — what the system did vs what it should have done]

**User impact**: [What the user experienced. "Users could not X" or "Data was corrupted for users who Y"]

---

## Impact Assessment

| Dimension | Detail |
|-----------|--------|
| **Severity** | Critical / High / Medium / Low |
| **Scope** | All users / Authenticated users / [specific role] / [specific action] |
| **Affected users** | ~N users, or "all" |
| **Duration** | From [first occurrence] to [fix deployed] |
| **Data impact** | Data lost / corrupted / none |
| **Regulatory** | GDPR / compliance implications (if any) |

---

## Timeline of Events

| Timestamp | Event |
|-----------|-------|
| YYYY-MM-DD | Defect introduced (commit: abc1234) |
| YYYY-MM-DD | First user report / monitoring alert |
| YYYY-MM-DD | Investigation started |
| YYYY-MM-DD | Root cause identified |
| YYYY-MM-DD | Fix implemented |
| YYYY-MM-DD | Fix deployed to production |
| YYYY-MM-DD | Incident closed |

---

## Investigation Process

### What We Checked

1. [First hypothesis] — Result: [Ruled out / Confirmed / Partial]
2. [Second hypothesis] — Result: [Ruled out / Confirmed / Partial]
3. [Evidence that pointed to root cause]

### 5 Whys

**Why #1**: [Immediate symptom — what failed]
**Why #2**: [What caused #1]
**Why #3**: [What caused #2]
**Why #4**: [What caused #3]
**Why #5**: [Root systemic cause]

---

## Root Cause

**Root cause**: [Single clear statement of the actual cause]

**Category**:
- [ ] Human Error — Incorrect implementation, misunderstanding of requirements
- [ ] Process Gap — Missing review step, absent test coverage, no validation
- [ ] System Limitation — External dependency failure, infrastructure issue
- [ ] Communication Issue — Unclear requirements, misaligned expectations
- [ ] Resource Constraint — Time pressure led to shortcuts
- [ ] Environmental — Config difference between environments

**Explanation**: [2-3 sentences explaining why this was the root cause, not just a symptom]

---

## Contributing Factors

Factors that didn't cause the bug but made it worse or let it slip through:

- [Factor 1: e.g., "No test covered this code path"]
- [Factor 2: e.g., "Staging data didn't include edge case that triggered the bug"]
- [Factor 3: e.g., "Code review focused on logic, not type safety"]

---

## Resolution

### Fix Applied

**What changed**: [Description of the fix]
**Files modified**:
- `path/to/file.py` — [What changed and why]

**Commit**: [SHA] `TICKET-ID: [commit message]`

### Verification

- [ ] Fix confirmed in development
- [ ] Fix confirmed in staging
- [ ] Fix confirmed in production
- [ ] Regression test added

---

## Prevention Measures

Actions to prevent this class of bug recurrence:

| Action | Owner | Ticket | Status |
|--------|-------|--------|--------|
| Add test: [describe coverage gap] | [name/team] | TICKET-ID | [ ] Open |
| Update process: [describe change] | [name/team] | — | [ ] Open |
| Add monitoring: [describe alert] | [name/team] | TICKET-ID | [ ] Open |
| Update documentation: [describe] | [name/team] | — | [ ] Open |

---

## Lessons Learned

### What Worked Well
- [Something in the investigation or response process that was effective]

### What Could Be Better
- [A gap in process, tooling, or communication that this incident revealed]

### Key Takeaway
[One sentence — the most important lesson from this incident]
