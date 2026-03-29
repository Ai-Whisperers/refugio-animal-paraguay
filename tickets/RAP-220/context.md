# RAP-220 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:00

## Current Focus
Enhancing sw.js with push event handlers and notificationclick handling.

## Technical State
- `public/sw.js` exists with PWA caching (install, activate, fetch events)
- `ServiceWorkerRegistration.tsx` registers SW on page load
- `PushNotificationSubscription.tsx` handles browser permission + subscribe/unsubscribe
- Backend: `src/api/push_subscriptions.py` manages subscriptions (in-memory)

## Next Steps
1. Enhance sw.js push event handler
2. Update ServiceWorkerRegistration.tsx 
3. Commit and push PR

## Blockers
None

## Key Decisions Made
- Keep push payload simple: {title, body, url, icon}
- notificationclick opens the `url` from payload data
- Badge count tracked via navigator.setAppBadge where available
