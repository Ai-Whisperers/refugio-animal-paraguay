---
story: S5
epic: EPIC-88
ticket: RAP-600
title: "Web push notifications"
status: ready
points: 6
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S05: Push Notifications via Service Worker

## Story

As a volunteer, I want to receive push notifications about emergency animal rescue cases so that I can respond immediately when urgent situations arise.

## Description

Implement web push notification infrastructure using Push API and Web Notification API. Allow users to subscribe to notifications, store subscriptions on backend, and send targeted push notifications for emergency cases, donation receipts, and adoption status changes.

## Acceptance Criteria

- [ ] Add "Subscribe to Notifications" button in /portal/settings (user profile page)
- [ ] Button initially says "Activar notificaciones" (Enable notifications)
- [ ] Click button requests browser notification permission using Notification.requestPermission()
- [ ] Handle permission states: granted, denied, default
- [ ] If granted: button changes to "Desactivar notificaciones" (Disable notifications)
- [ ] Store PushSubscription data on backend: implement POST /api/push/subscribe
- [ ] PushSubscription schema: endpoint (string), auth (base64), p256dh (base64), user_id FK
- [ ] Implement DELETE /api/push/unsubscribe to remove subscription
- [ ] Service worker listens for push events: self.addEventListener('push', handlePush)
- [ ] Display notification on push event with title, body, icon, badge
- [ ] Backend: send emergency case notification when case status changes to "emergency"
- [ ] Backend: send donation receipt notification after successful donation
- [ ] Backend: send adoption status update notifications (approved, rejected, needs_info)
- [ ] Use web-push npm package on backend to send notifications
- [ ] Test notification click: clicking notification opens relevant page (case detail, etc.)
- [ ] Notification title for emergency: "EMERGENCIA: Animal necesita rescate" (Emergency)
- [ ] Notification title for donation: "Gracias por tu donacion" (Thank you for donation)
- [ ] Notification title for adoption: "Tu solicitud de adopcion" (Your adoption request)
- [ ] Test on iOS Safari (limited support, browser-based only)
- [ ] Test on Android Chrome with full push capability

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Push API integration implemented
- [ ] Backend subscription storage and management
- [ ] Service worker push event handling
- [ ] Unit tests for subscription management
- [ ] Integration test for push notification flow
- [ ] Manual testing on actual Android device with push
- [ ] Manual testing on iOS Safari (notification permissions)
- [ ] Error handling for failed push sends
- [ ] Monitoring of push delivery success rate
- [ ] Documentation of notification event types
- [ ] Deployed to staging and verified

## Technical Notes

- Requires HTTPS (self-signed certs not suitable for push)
- Use Firebase Cloud Messaging (FCM) or other push service provider
- Store encrypted subscription data in database
- Implement retry logic for failed notifications (queue retries)
- Handle subscription expiration (resend if not refreshed in 30 days)
- Test notification payload limits (title <90 chars, body <240 chars)
- iOS Safari limitations: only browser-based notifications, no background push
- Monitor push delivery metrics and failure rates

## Story Points: 5
