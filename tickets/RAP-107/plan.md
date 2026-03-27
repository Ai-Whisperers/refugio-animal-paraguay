# RAP-107 Plan

## Objective
Add animal status workflow UI allowing staff to transition animals through lifecycle states with validation.

## Description
Staff need a visual way to change animal status that only shows valid transitions. The backend already has the transition rules defined in `src/services/animal_status.py`. This story adds a frontend modal component and integrates it into the animal management pages.

## Acceptance Criteria
- [ ] Staff can click "Change Status" on an animal and see only valid next statuses
- [ ] Changing status to adopted records timestamp and updates the list
- [ ] Status transitions appear with visual indicators (colors, arrows)
- [ ] Invalid transitions are not shown to the user
- [ ] Error states handled (API failures, network errors)

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — multiple components (modal, list integration, edit page), frontend state management

## Approach
1. Create `VALID_TRANSITIONS` map in frontend matching backend rules
2. Create `StatusWorkflowModal` component with confirmation dialog
3. Add "Change Status" button to animal list actions column
4. Write Vitest component tests

## Dependencies
- Depends on: RAP-105 (animal list, done), RAP-106 (animal form, done)
