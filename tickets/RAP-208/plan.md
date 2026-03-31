# RAP-208 Plan

## Objective
Add notification frequency controls (immediate, daily_digest, weekly) per channel so users can choose how often batched email notifications are delivered.

## Description
Extends the notification preferences system with a per-user, per-channel frequency setting. The frequency determines whether notifications are sent immediately or queued for a daily/weekly digest batch. This is stored in a dedicated `notification_channel_frequency` table separate from per-type opt-in/opt-out preferences.

## Acceptance Criteria
- [ ] `NotificationFrequency` enum (immediate, daily_digest, weekly) exists in model layer
- [ ] `notification_channel_frequency` table created via Alembic migration
- [ ] Service functions to get/set frequency per user per channel
- [ ] API endpoints: GET and PUT `/notification-preferences/frequency`
- [ ] Schemas with OpenAPI documentation
- [ ] Unit tests covering service logic
- [ ] Integration tests covering API endpoints
- [ ] `is_immediate` helper for routing logic

## Complexity Assessment
**Track**: Simple Fix

### Simple Fix Criteria
- [x] Single, clear root cause identified
- [ ] Solution affects ≤3 files (affects ~5-6 files but all related)
- [x] Change impact ≤10 lines of actual code — false, more like 150
- [x] Low risk of side effects
- [x] Solution pattern is well-understood

**Assessment result**: Complex — new table, migration, model, service, schema, router additions

## Approach
1. Add `NotificationFrequency` enum and `NotificationChannelFrequency` model
2. Create Alembic migration
3. Add service functions (get_frequency, set_frequency)
4. Add schemas (FrequencyItem, FrequencyListResponse)
5. Add API endpoints to existing notification_preferences router
6. Write unit + integration tests

## Dependencies
- Depends on: RAP-205 (notification preference model) ✓ DONE

## Risks
- Migration must be clean (no conflicts with existing tables)
