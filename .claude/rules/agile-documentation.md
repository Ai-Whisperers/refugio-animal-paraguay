# Rule: Agile Documentation
**ID**: rule.agile.documentation.v1
**Version**: 1.0.0
**Applies to**: All feature planning and backlog management

---

## Hierarchy

```
Epic        ← Strategic goal, 2+ sprints, contains multiple features
  └── Feature     ← User-facing capability, 1-2 sprints, contains stories
       └── User Story  ← Single behavior, one sprint or less
            └── Task    ← Implementation step, hours
```

---

## Epic Structure

```markdown
# [EPIC-N] Epic Title

## Overview
**Goal**: One sentence — the strategic outcome this epic delivers.
**Why it matters**: Business/user impact.
**Target users**: Who benefits from this epic.

## Scope
### In Scope
- Capability 1
- Capability 2

### Out of Scope
- What we explicitly won't do (prevents scope creep)

## Features
- [ ] [FEAT-1] Feature name — brief description
- [ ] [FEAT-2] Feature name — brief description
- [ ] [FEAT-3] Feature name — brief description

## Dependencies
- Depends on: [system/team]
- Blocks: [downstream work]
```

---

## Feature Structure

### Business Feature (user-facing)

```markdown
# [FEAT-N] Feature Title

## Parent Epic
[EPIC-N] Epic Title

## Overview
**Description**: What the user can do with this feature.
**User value**: Why users need this.
**Business value**: Revenue/impact/risk reduction.

## User Stories
- [ ] [US-1] Story title
- [ ] [US-2] Story title
- [ ] [US-3] Story title

## Acceptance Criteria (Feature Level)
The feature is complete when:
- [ ] Criterion 1 (testable)
- [ ] Criterion 2
- [ ] Criterion 3

## Definition of Done
- [ ] All user stories complete
- [ ] Feature tested end-to-end in staging
- [ ] Accessibility requirements met
- [ ] Documentation updated
- [ ] Product owner sign-off

## Dependencies
## Risks
```

### Technical Feature (non-user-facing)

```markdown
# [TFEAT-N] Technical Feature Title

## Parent Epic
## Problem Statement
What technical problem does this solve?

## Proposed Solution
Technical approach at high level.

## Tasks
- [ ] Task 1
- [ ] Task 2

## Definition of Done
- [ ] Implementation complete
- [ ] Tests added/updated
- [ ] No regressions
```

---

## User Story Structure

### Format
```
As a [role], I want [goal/action] so that [benefit/outcome].
```

### Complete Story Format

```markdown
# [US-N] Story Title

## Story
As a **[role]**, I want **[goal]** so that **[benefit]**.

## Acceptance Criteria
**Given** [initial context/state]
**When** [user action or event]
**Then** [expected outcome]

Additional criteria:
- [ ] Criterion 1
- [ ] Criterion 2

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for happy path
- [ ] Edge cases handled (empty state, errors)
- [ ] Deployed to staging and verified

## Technical Notes (optional)
Key technical considerations, API endpoints, data model changes.

## Story Points: [estimate]
```

### User Story Anti-Patterns

```
❌ "As a user, I want the system to work"
   — Too vague. What user? What behavior?

❌ "As an admin, I want to manage all the things"
   — Too broad. Split into specific stories.

❌ "As a developer, I want to refactor the auth module"
   — Developers are not the user. Use Technical Feature instead.

✅ GOOD: "As a volunteer, I want to register for a shift online
   so that I don't have to call the shelter."
   — Clear role, clear action, clear benefit.
```

---

## Story Splitting Patterns

**By workflow step**:
```
Before: User can complete adoption process
After:
  US-1: User can submit adoption request
  US-2: Shelter reviews and approves request
  US-3: User receives approval notification
  US-4: User schedules pickup visit
```

**By role/permission level**:
```
Before: Users can manage adoptions
After:
  US-1: Adopters can submit applications
  US-2: Staff can review applications
  US-3: Admin can override decisions
```

---

## Project-Specific Roles

| Role | Description |
|------|-------------|
| **adopter** | Person looking to adopt an animal |
| **donor** | Person/organization making a donation (including EU donors) |
| **volunteer** | Person helping at the shelter |
| **staff** | Shelter employee |
| **admin** | Shelter administrator/manager |
| **vet** | Veterinarian working with the shelter |
| **foster** | Person temporarily caring for an animal |

---

## FINAL MUST-PASS CHECKLIST

Before a user story enters a sprint:
- [ ] Story follows "As a [role], I want [goal] so that [benefit]" format
- [ ] Role is from the project roles list (or explicitly new)
- [ ] Acceptance criteria are testable (Given/When/Then or bullets)
- [ ] Definition of Done includes tests, review, staging deployment
- [ ] Story is ≤5 points (split if larger)
- [ ] No technical implementation details in user-facing story
- [ ] Story links to parent Feature
- [ ] Edge cases considered (empty state, errors, permissions)
