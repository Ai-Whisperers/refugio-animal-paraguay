# RAP-217 Plan

## Objective
Implement email campaign scheduling and sending — allows staff to create campaigns that send email templates to subscriber lists at a scheduled time.

## Acceptance Criteria
- [ ] Staff can create email campaigns (select list + template + schedule time)
- [ ] Campaign states: draft → scheduled → sending → sent | failed | cancelled
- [ ] Campaign can be triggered immediately or scheduled for future
- [ ] API endpoints with proper validation
- [ ] Unit and integration tests passing

## Complexity Assessment
**Track**: Complex — new model + migration + service + router

## Approach
1. Create EmailCampaign model + migration 085
2. Create campaign sending service (async sending placeholder)
3. Create API router for campaign scheduling
4. Write tests
