# RAP-117 Plan

## Objective
Create an individual donor profile page showing lifetime stats and donation history.

## Description
Staff need to view detailed donor profiles with lifetime donation totals, frequency, preferred currency, and all past donations. This page is reached by clicking a donor row in the donor list.

## Acceptance Criteria
- [ ] Donor profile page at /admin/donors/[id]
- [ ] Shows donor name, email, country, currency preference, GDPR consent status
- [ ] Lifetime donation total (per currency)
- [ ] Donation count and frequency
- [ ] List of all past donations
- [ ] Loading, error, and empty states

## Complexity Assessment
**Assessment result**: Complex — new page but follows established patterns

## Approach
1. Fetch donor details via GET /donors/{id}
2. Fetch donor donations via GET /donations?donor_id={id}
3. Compute lifetime stats from donation data
4. Display in profile layout

## Dependencies
- Backend GET /donors/{id} (exists)
- Backend GET /donations?donor_id={id} (exists)
