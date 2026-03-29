# RAP-220 Plan

## Objective
Enhance the service worker to fully support browser push notifications, including receiving push events and showing system notifications.

## Description
The existing sw.js handles PWA caching only. To enable browser push notifications, the service worker must also handle `push` events (from the browser push service) and `notificationclick` events (when user interacts with a notification). This completes the push notification pipeline: backend sends → push service delivers → SW receives → browser shows notification.

## Acceptance Criteria
- [ ] Service worker handles `push` events and shows browser notifications
- [ ] `notificationclick` events navigate to the correct URL
- [ ] Push notification badge count is tracked
- [ ] Graceful fallback when push payload is missing or malformed
- [ ] ServiceWorkerRegistration component subscribes to push after SW registers
- [ ] All edge cases handled (empty state, errors, permissions)

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — enhancing existing sw.js file + ServiceWorkerRegistration component. Single concern, ≤3 files, low risk.

## Approach
1. Enhance `public/sw.js` with push and notificationclick event handlers
2. Update `ServiceWorkerRegistration.tsx` to export push subscription helper
3. Add backend VAPID public key endpoint for clients to fetch

## Dependencies
- Depends on: existing sw.js, PushNotificationSubscription.tsx

## Risks
- Risk: VAPID key not configured → Mitigation: graceful fallback with console warning
