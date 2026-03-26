# Command: /create-story
**Usage**: `/create-story`
**Also**: `/create-epic`, `/create-feature`

---

## What This Does

Guides creation of well-structured Agile artifacts (Epics, Features, or User Stories) following project standards. Asks the right questions to produce complete, testable, sprint-ready artifacts.

**Rules applied**: `.claude/rules/agile-documentation.md`

---

## Step 1: Determine Artifact Type

Ask: "Are you creating an Epic, Feature, or User Story?"

Or auto-detect from context:
- "Big strategic goal spanning weeks" → Epic
- "User-facing capability, 1-2 sprints" → Feature
- "Single user behavior, sprint-ready" → User Story

---

## Creating a User Story

### Step 2: Gather Information

Ask (one at a time, don't overwhelm):

1. "Who is this for? (adopter / donor / volunteer / staff / admin / vet / foster)"
2. "What do they want to be able to do?"
3. "What's the benefit? Why do they need this?"
4. "What would make this story 'done'? (acceptance criteria)"

Optional follow-up:
- "Any edge cases to consider? (empty state, invalid input, permission edge cases)"
- "Any dependencies or blockers?"
- "Story point estimate? (1/2/3/5/8 — if >5, should we split?)"

### Step 3: Draft the Story

```markdown
# [US-NNN] [Story Title]

## Story
As a **[role]**, I want **[goal]** so that **[benefit]**.

## Context
[Why does this story exist? What problem does it solve?]

## Acceptance Criteria
**Given** [initial state]
**When** [user action]
**Then** [expected outcome]

Additional criteria:
- [ ] [Edge case handled]
- [ ] [Error state handled]
- [ ] [Permission requirement]

## Definition of Done
- [ ] Code complete and peer reviewed
- [ ] Unit tests: happy path + at least 2 edge cases
- [ ] Integration test for the main flow
- [ ] Responsive design (if UI)
- [ ] Accessibility: WCAG 2.1 AA (if UI)
- [ ] Deployed to staging and verified
- [ ] No regression in related features

## Story Points: [estimate]
## Parent Feature: [FEAT-NNN] [Name]
```

### Step 4: Check Splitting

If story is >5 points, help split it:

"This feels large. Common ways to split:
1. **By workflow step**: First: submit form. Then: review. Then: notify.
2. **By data type**: First: EUR donations. Then: USD. Then: currency display.
3. **By happy path first**: Basic flow now, edge cases as follow-up stories."

---

## Creating an Epic

### Step 2: Gather Information

Ask:
1. "What strategic goal does this epic achieve?"
2. "Who benefits from this epic?"
3. "What's out of scope? (what should we NOT do)"
4. "What does success look like? (measurable metrics)"
5. "What features would make up this epic?"

### Step 3: Draft the Epic

```markdown
# [EPIC-N] [Epic Title]

## Overview
**Goal**: [One sentence — strategic outcome]
**Why it matters**: [Business/user impact]
**Target users**: [Who benefits]

## Scope
### In Scope
- [Capability 1]
- [Capability 2]

### Out of Scope
- [What we explicitly won't do]

## Features
- [ ] [FEAT-1] [Feature name] — [brief description]
- [ ] [FEAT-2] [Feature name] — [brief description]

## Success Metrics
- [Metric]: [measurable target]

## Dependencies
## Status: Planning
```

---

## Creating a Feature

### Step 2: Gather Information

Ask:
1. "Which epic does this belong to?"
2. "What capability does this add for users?"
3. "What stories would make up this feature?"
4. "What does 'feature complete' look like?"

### Step 3: Draft the Feature

```markdown
# [FEAT-N] [Feature Title]

## Parent Epic
[EPIC-N] [Title]

## Overview
**Description**: [What the user can do]
**User value**: [Why users need this]

## User Stories
- [ ] [US-1] [Story title]
- [ ] [US-2] [Story title]

## Acceptance Criteria
The feature is complete when:
- [ ] [End-to-end criterion]
- [ ] [Performance criterion]

## Definition of Done
- [ ] All user stories complete
- [ ] End-to-end test
- [ ] Product Owner sign-off

## Status: Planning
```

---

## Quality Checklist — Before Saving

### User Stories
- [ ] Role is specific (not just "user")
- [ ] Goal is a user action, not technical implementation
- [ ] Benefit is clear and valuable
- [ ] Acceptance criteria are testable (Given/When/Then)
- [ ] Story is ≤5 points
- [ ] Edge cases considered
- [ ] Linked to parent feature

### Epics
- [ ] Strategic goal is clear
- [ ] Out-of-scope explicitly defined
- [ ] Success metrics are measurable
- [ ] Features list is realistic

---

## Refugio Animal Paraguay Story Examples

### Good stories for this project

```
As an **adopter**, I want to submit an adoption application online
so that I don't have to visit the shelter before my first interview.

As a **EU donor**, I want to receive a donation receipt in English with EUR
so that I can use it for tax deduction in my country.

As a **volunteer**, I want to see my scheduled shifts in a calendar view
so that I can plan my week around shelter commitments.

As a **staff member**, I want to mark an animal as "reserved" while an
adoption application is pending so that two families don't apply for the same animal.
```

---

## FINAL MUST-PASS CHECKLIST

- [ ] Story uses "As a [role], I want [goal] so that [benefit]" format
- [ ] Role is specific to this project
- [ ] Acceptance criteria are testable
- [ ] Definition of Done is complete
- [ ] Story is ≤5 points (or split)
- [ ] Parent feature/epic linked
- [ ] Edge cases and error states considered
