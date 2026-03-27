# RAP-112 Plan

## Objective
Add approve/reject workflow with mandatory notes to the adoption request detail view.

## Acceptance Criteria
- [ ] Approve and Reject buttons visible on pending requests
- [ ] Modal requires mandatory notes (min 10 chars) before confirming
- [ ] Approve changes animal status to reserved, notifies adopter
- [ ] After action, page refreshes to show updated status
- [ ] Buttons hidden for non-pending requests

## Complexity Assessment
**Track**: Complex — Modal component, API integration, state management

## Approach
1. Create AdoptionStatusModal component
2. Integrate into adoption detail page
3. Connect to PATCH /adoption-requests/{id}/status endpoint
