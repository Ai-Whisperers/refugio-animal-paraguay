# RAP-215 Plan

## Objective
Implement email list management and segmentation allowing staff to create, manage, and segment subscriber lists for email campaigns.

## Description
Staff need the ability to manage email subscriber lists and create segments based on recipient attributes (donors, adopters, volunteers, etc.). This is the foundation for email campaigns in EPIC-44.

## Acceptance Criteria
- [ ] Staff can create/read/update/delete email lists
- [ ] Email lists support segmentation by user type (donor, adopter, volunteer)
- [ ] Staff can add/remove subscribers to/from lists
- [ ] Email unsubscribe handling integrated
- [ ] API endpoints documented in OpenAPI schema
- [ ] Unit and integration tests passing (80%+ coverage)

## Complexity Assessment
**Track**: Complex Implementation

### Assessment
- Multiple new DB models (EmailList, EmailListMember)
- New migration required
- New API router
- Segmentation logic across multiple user types
- Unsubscribe handling integration

**Assessment result**: Complex — multiple files, models, and service logic.

## Approach
1. Create EmailList and EmailListMember SQLAlchemy models
2. Create Alembic migration (083)
3. Create email_lists API router with CRUD + segmentation
4. Create email_list_service for segmentation logic
5. Write unit tests and integration tests

## Dependencies
- Depends on: existing user/donor/adopter models
- Blocked by: nothing

## Risks
- Risk: Migration conflicts with existing 082 files → Mitigation: use 083 prefix
