# RAP-052 Plan

## Objective
Implement notification preferences that allow users to control which notification types they receive, enabling per-channel (in-app, email) opt-in/opt-out per notification category.

## Description
Staff and admin users need control over their notification volume. This story adds a preference model that stores per-user, per-notification-type, per-channel settings. The notification service and event bus handlers will check preferences before creating notifications. This prevents notification fatigue and is a prerequisite for downstream notification stories.

## Acceptance Criteria
- [ ] NotificationPreference model with user_id, notification_type, channel (in_app/email), enabled (boolean)
- [ ] Default: all notification types enabled for all channels
- [ ] GET /notification-preferences — list preferences for current user
- [ ] PUT /notification-preferences — bulk update preferences
- [ ] Service checks preferences before creating in-app notifications
- [ ] Unique constraint on (user_id, notification_type, channel)
- [ ] Unit tests for preference service logic
- [ ] Integration tests for API endpoints

## Complexity Assessment
**Track**: Complex — new model, service, API, integration with existing notification pipeline

## Approach
1. NotificationPreference ORM model + migration
2. Preference service (get, update, check)
3. API endpoints (GET list, PUT bulk update)
4. Integrate preference check into notification creation flow
5. Tests

## Dependencies
- Depends on: In-App Notifications (RAP-051, PR #32)
- Blocked by: Nothing

## Risks
- Risk: Preference check adds latency to notification creation → Mitigation: Batch-fetch preferences per event
