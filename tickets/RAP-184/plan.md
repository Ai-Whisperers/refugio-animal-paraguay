# RAP-184 Plan

## Objective
Add a staff-triggered batch endpoint that sends in-app shift reminder notifications to volunteers with upcoming shifts.

## Description
Volunteers signed up for shifts need reminders before their shift. This ticket adds a `POST /api/shifts/reminders/send` endpoint (staff-only) that finds all signups without a reminder for shifts in the next N hours, creates an in-app notification for each volunteer, and marks the signup as reminded. Follows the same pattern as `followup_automation`.

## Acceptance Criteria
- [ ] `POST /api/shifts/reminders/send?hours_ahead=24` sends in-app reminders for upcoming shifts
- [ ] Only signups with `reminder_sent_at IS NULL` are processed (idempotent)
- [ ] Cancelled shifts are excluded
- [ ] Response includes `sent_count`, `hours_ahead`, `sent_at`
- [ ] Staff-only endpoint (requires `require_staff`)
- [ ] Unit tests for service logic (mock DB)
- [ ] Integration tests for endpoint behaviour

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — one new service file, one new router, one migration, no architectural changes.

## Approach
1. Migration 073: add `reminder_sent_at` (nullable TIMESTAMP TZ) to `shift_signups`
2. Update `ShiftSignup` ORM model
3. Add `VOLUNTEER_SHIFT_REMINDER` to `NotificationType`
4. `src/services/shift_reminder_service.py` — `send_shift_reminders(db, hours_ahead, batch_size)`
5. `src/api/shift_reminders.py` — `POST /api/shifts/reminders/send`
6. Register router in `src/app.py`
7. Tests

## Dependencies
- Depends on: `notification_service.create_notification`, `ShiftSignup` model

## Risks
- None significant
