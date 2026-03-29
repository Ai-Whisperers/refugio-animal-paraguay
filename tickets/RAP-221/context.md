# RAP-221 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:05

## Current Focus
Created PushOptInModal and PushNotificationButton with full opt-in flow.

## Technical State
- PushOptInModal: value-prop modal with focus trap, ESC, ARIA
- PushNotificationButton: wrapper button that shows modal before permission prompt
- Both components lazy-load modal to keep bundle small
- Integrates with subscribeToPush/unsubscribeFromPush from ServiceWorkerRegistration

## Next Steps
1. Commit
2. Create PR
3. Mark story done

## Key Decisions Made
- Modal approach: show value prop before browser's native permission dialog
- Lazy loading PushOptInModal via next/dynamic to keep initial bundle size small
- PushNotificationButton wraps the full flow; PushNotificationSubscription remains for simpler use cases
