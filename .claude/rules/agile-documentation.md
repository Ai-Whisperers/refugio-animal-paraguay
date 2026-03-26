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

**Sizing guide**:
- Epic: weeks/months, too big to estimate precisely
- Feature: 1-2 week sprints, estimable
- User Story: 1-5 story points, fits in a sprint
- Task: 1-8 hours

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

## Success Metrics
- Metric 1: [measurable target]
- Metric 2: [measurable target]

## Dependencies
- Depends on: [system/team]
- Blocks: [downstream work]

## Status
- [ ] Planning
- [ ] In Progress
- [ ] Complete
```

### Epic Examples for Refugio Animal Paraguay

```
[EPIC-1] Animal Adoption Platform
[EPIC-2] Donor Management & EU Fundraising
[EPIC-3] Shelter Operations Dashboard
[EPIC-4] Volunteer Coordination
[EPIC-5] Reporting & Analytics
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
What technical problem does this solve? What's the risk if we don't do it?

## Proposed Solution
Technical approach at high level.

## Tasks
- [ ] Task 1
- [ ] Task 2

## Definition of Done
- [ ] Implementation complete
- [ ] Tests added/updated
- [ ] Performance benchmarks met (if applicable)
- [ ] No regressions
- [ ] Runbook updated (if ops impact)
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

## Context
Why does this story exist? What problem does it solve?

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
- [ ] UI responsive (if applicable)
- [ ] Accessibility: WCAG 2.1 AA
- [ ] Deployed to staging and verified
- [ ] No regressions in related features

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

❌ Story without acceptance criteria
   — How will we know when it's done?

✅ GOOD: "As a volunteer, I want to register for a shift online
   so that I don't have to call the shelter."
   — Clear role, clear action, clear benefit.
```

---

## Story Splitting Patterns

### Patterns for splitting

**By workflow step**:
```
Before: User can complete adoption process
After:
  US-1: User can submit adoption request
  US-2: Shelter reviews and approves request
  US-3: User receives approval notification
  US-4: User schedules pickup visit
```

**By data type/variation**:
```
Before: System supports international donors
After:
  US-1: System accepts EUR donations
  US-2: System accepts USD donations
  US-3: System handles currency conversion display
```

**By happy path + edge cases**:
```
Before: User can manage their animal's medical records
After:
  US-1: User can view animal's medical history [MVP]
  US-2: User can add a new medical record
  US-3: User can attach vet documents to records
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

For Refugio Animal Paraguay, story roles include:

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
