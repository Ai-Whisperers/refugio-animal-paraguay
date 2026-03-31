# RAP-215 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 05:42

## Current Focus
Implementing email list management and segmentation backend API.

## Technical State
- Branch: feature/RAP-215-email-list-management
- New models: EmailList, EmailListMember
- Migration: 083_create_email_lists_tables.py
- Router: src/api/email_lists.py
- Service: src/services/email_list_service.py

## Next Steps
1. Create DB models
2. Create migration
3. Create API router
4. Create service
5. Write tests

## Blockers
None

## Key Decisions Made
- Use StrEnum for list type (general, donors, adopters, volunteers, custom)
- Unsubscribe token stored per member for GDPR-safe opt-out
