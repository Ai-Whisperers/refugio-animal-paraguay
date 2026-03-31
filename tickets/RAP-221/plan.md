# RAP-221 Plan

## Objective
Implement a polished push notification opt-in flow with a modal dialog that explains the value proposition before requesting browser permission.

## Description
Currently PushNotificationSubscription renders a single toggle button with no context. Users need to understand WHY they should grant notification permission before being prompted. This story adds a modal-based opt-in flow that: (1) presents value proposition, (2) explains what notifications they'll receive, (3) requests permission only after user explicitly agrees.

## Acceptance Criteria
- [ ] PushOptInModal component shows before browser permission prompt
- [ ] Modal explains what notifications the user will receive
- [ ] "Activar" button triggers permission request + subscription
- [ ] "Ahora no" closes modal without requesting permission
- [ ] Modal is accessible (focus trap, ARIA roles, keyboard escape)
- [ ] Component integrates into portal settings or admin settings

## Complexity Assessment
**Track**: Simple Fix — new frontend component, ≤3 files touched, low risk.

## Approach
1. Create PushOptInModal component with value proposition
2. Update PushNotificationSubscription to show modal first
3. Hook modal into admin settings notifications page

## Dependencies
- Depends on: RAP-220 (SW push support) — completed

## Risks
- Risk: Browser permission modal timing varies → Mitigation: show after user clicks "Activar"
