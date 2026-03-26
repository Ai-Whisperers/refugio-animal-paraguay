# RAP-099 Plan — EXEMPLAR: Bad Plan

_These patterns are WRONG. Do NOT produce output like this._

---

## ❌ Anti-Pattern 1: Vague Objective

```markdown
## Objective
Fix the email thing that's broken.
```

**Problems**: What email thing? What does "broken" mean? What does "fixed" look like?

**Fix**: "Add RFC 5322 email validation to donor registration to prevent disposable addresses from entering the system."

---

## ❌ Anti-Pattern 2: No Acceptance Criteria (or Untestable Ones)

```markdown
## Acceptance Criteria
- [ ] Email works correctly
- [ ] Users can't enter bad emails
- [ ] Tests pass
```

**Problems**:
- "Works correctly" is not testable — correct according to what standard?
- "Bad emails" is undefined — which emails are bad?
- "Tests pass" is not an acceptance criterion — it's a prerequisite

**Fix**: Write specific, binary criteria: "RFC 5322 pattern enforced", "mailinator.com rejected", "valid EU TLDs accepted"

---

## ❌ Anti-Pattern 3: Missing or Skipped Complexity Assessment

```markdown
## Complexity Assessment
This is probably simple.
```

**Problems**:
- No criteria evaluated
- No evidence for the "simple" claim
- Might be simple but could be complex if validation touches auth middleware

**Fix**: Evaluate all 5 criteria explicitly. List the files affected. Estimate line count.

---

## ❌ Anti-Pattern 4: Undefined Dependencies and No Risk Assessment

```markdown
## Dependencies
None.

## Risks
None.
```

**Problems**:
- Nearly nothing has no dependencies — at minimum, it depends on the language/framework being stable
- "No risks" on a security-adjacent feature (input validation) is a red flag — means risks weren't considered

**Fix**: Think about what happens if validation is too strict (rejects valid emails), too loose (accepts bad ones), or if the library has a bug.

---

## ❌ Anti-Pattern 5: Approach That's Just a Restatement of the Objective

```markdown
## Approach
Add email validation to fix the email problem.
```

**Problems**:
- This isn't an approach — it's circular
- No files mentioned, no sequence of steps, no indication of where validation goes

**Fix**: Name the files, the library, the sequence (frontend then backend, or backend then frontend), and the test strategy.
