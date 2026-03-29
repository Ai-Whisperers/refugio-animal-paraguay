# RAP-207 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29 00:00

## Current Focus
Implementing channel routing in in-app and email dispatchers.

## Technical State
- `is_notification_enabled(db, user_id, notification_type, channel)` already exists in `notification_preference_service.py`
- Target: `InAppNotificationHandlers._notify_all_staff` (in_app channel)
- Target: `NotificationHandlers._get_staff_emails` (email channel for staff alerts)
- Adopter/donor emails (non-user recipients) are not preference-gated — they have no User account

## Next Steps
1. Modify in_app_handlers.py
2. Modify handlers.py
3. Write unit tests
4. Run quality gates

## Blockers
None.

## Key Decisions Made
- Only staff User accounts have preferences — adopter/donor email recipients are always notified
- N+1 per user is acceptable for now (small staff count)
