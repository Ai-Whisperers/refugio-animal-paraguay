# Exemplar: Bad User Story

_These patterns are WRONG. Do NOT produce output like this._

---

## Anti-Pattern 1: Vague Role and Goal

```
❌ As a user, I want to manage animals so that I can do my job.
```

**Problems**:
- "User" is not a role — which user? Adopter? Staff? Volunteer?
- "Manage animals" is not a goal — what specific action?
- "Do my job" is not a benefit — what outcome does it enable?

**Fix**: "As a **shelter staff member**, I want to **update an animal's availability status** so that **adopters see accurate listings without calling us**."

---

## Anti-Pattern 2: Technical Story (Should Be Technical Feature)

```
❌ As a developer, I want to refactor the auth module so that the codebase is cleaner.
```

**Problems**:
- Developers are not users — user stories capture user value
- "Cleaner codebase" is not a user benefit
- No acceptance criteria possible from a user perspective

**Fix**: Use a Technical Feature: `[TFEAT-N] Refactor auth module for maintainability`

---

## Anti-Pattern 3: No Acceptance Criteria

```
❌ As a donor, I want to donate money to the shelter.

Acceptance criteria: Donation works.
```

**Problems**:
- "Donation works" is not testable
- No Given/When/Then, no specifics
- Can't be verified in a sprint review

**Fix**: Write 3–5 specific, testable criteria. What currencies? What confirmation? What error states?

---

## Anti-Pattern 4: Too Large (Epic Disguised as Story)

```
❌ As an admin, I want a complete reporting dashboard so that I can see all shelter metrics.
```

**Problems**:
- "Complete reporting dashboard" is weeks of work
- Cannot fit in a single sprint
- No focus — dozens of features bundled

**Fix**: Split by report type:
- Story 1: "As an admin, I want to see daily adoption count so that I can track monthly goals"
- Story 2: "As an admin, I want to export donor totals to CSV so that I can submit grant reports"

---

## Anti-Pattern 5: Solution-Prescribing

```
❌ As a volunteer, I want a React modal dialog with a date picker component
   so that I can sign up for shifts.
```

**Problems**:
- Prescribes implementation (React modal, date picker)
- User doesn't care about implementation — they care about the outcome
- Blocks better implementation choices

**Fix**: "As a volunteer, I want to register for a shift online so that I don't have to call the shelter."
The modal and date picker are implementation decisions, not requirements.
