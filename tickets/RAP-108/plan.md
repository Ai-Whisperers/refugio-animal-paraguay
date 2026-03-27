# RAP-108 Plan

## Objective
Add batch selection and bulk status update functionality to the animal management list.

## Acceptance Criteria
- [ ] Checkboxes on each animal row and "select all" in header
- [ ] Batch action toolbar appears when animals are selected
- [ ] Batch status change uses StatusWorkflowModal for valid transitions
- [ ] Each animal's status is updated individually via API
- [ ] Error handling for partial failures
- [ ] Selection state clears after successful batch operation

## Complexity Assessment
**Track**: Complex — modifies existing page, adds selection state, batch API calls

## Approach
1. Add checkbox selection state to animal list page
2. Create batch action toolbar component
3. Reuse StatusWorkflowModal for batch status changes
4. Handle partial failures gracefully
