# RAP-207 Plan

## Objective
Wire `is_notification_enabled` into the in-app and email notification dispatchers so user preferences are honoured at send time.

## Description
The `NotificationPreference` model and API already exist (RAP-205). The `is_notification_enabled` helper in `notification_preference_service.py` can query per-user opt-out state. Currently, all handlers ignore preferences and send to everyone. This ticket adds the preference gate to `InAppNotificationHandlers._notify_all_staff` and to `NotificationHandlers._get_staff_emails`.

## Acceptance Criteria
- [ ] In-app notifications: each staff user's in_app preference is checked before a notification record is created
- [ ] Email staff alerts: each staff user's email preference is checked before an alert email is sent
- [ ] Missing preference rows are treated as enabled (existing opt-out model preserved)
- [ ] Unit tests cover: preference-disabled user skipped, preference-enabled user notified, default-enabled (no row) user notified
- [ ] Zero linting errors, zero type errors

## Complexity Assessment
**Track**: Simple Fix — 2 files modified, logic is additive (gate before send), pattern is clear.

## Approach
1. Add `notification_type` parameter to `InAppNotificationHandlers._notify_all_staff`, call `is_notification_enabled` per user before `create_notification`.
2. Refactor `NotificationHandlers._get_staff_emails` → `_get_staff_email_recipients(notification_type)` returning `(user_id, email)` pairs, filter by preference.
3. Update callers in both files.
4. Write unit tests.

## Dependencies
- `src/services/notification_preference_service.is_notification_enabled`
- `src/db/models/notification_preference.NotificationChannel`

## Risks
- Risk: N+1 queries per staff user → Mitigation: staff count is small (<20), acceptable for now. Bulk query optimisation can come later.
