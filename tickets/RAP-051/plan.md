# RAP-051 Plan

## Objective
Implement an in-app notification system that stores notifications in the database and exposes them via REST API, enabling real-time awareness of shelter events for staff and admin users.

## Description
In-app notifications are a foundational communication feature. Staff and admins need to see notifications about adoption status changes, new donations, animal intakes, and other shelter events directly within the application. This story builds the notification backend: model, service layer, API endpoints, and event bus integration for automatic notification creation.

## Acceptance Criteria
- [ ] Notification model with fields: id, user_id, type, title, message, data (JSON), is_read, read_at, created_at
- [ ] NotificationType enum covering shelter events (adoption, donation, animal, system)
- [ ] Service: create_notification, list_notifications (paginated, filterable by read status), mark_read, mark_all_read, get_unread_count
- [ ] GET /notifications — list with pagination and ?is_read filter
- [ ] GET /notifications/unread-count — returns count of unread notifications
- [ ] PATCH /notifications/{id}/read — mark single notification as read
- [ ] POST /notifications/mark-all-read — mark all as read for current user
- [ ] DELETE /notifications/{id} — soft or hard delete a notification
- [ ] Event bus subscribers auto-create notifications on key domain events
- [ ] Unit tests for service logic
- [ ] Integration tests for API endpoints

## Complexity Assessment
**Track**: Complex — new model, service, API, event bus integration, pagination

## Approach
1. Notification ORM model + Alembic migration
2. Notification service with CRUD + filtering
3. API router with auth (require_staff for all endpoints)
4. Event bus subscribers for automatic notification creation
5. Unit + integration tests

## Dependencies
- Depends on: Event Bus Infrastructure (RAP-014, DONE), JWT Auth (RAP-007, DONE)
- Blocked by: Nothing

## Risks
- Risk: High notification volume for active shelters → Mitigation: Pagination, auto-expiry for old notifications
