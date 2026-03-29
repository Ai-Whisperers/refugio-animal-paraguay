# RAP-206 Plan

## Objective
Build a Next.js admin page for staff to view and update their notification preferences per channel.

## Acceptance Criteria
- [ ] GET /admin/settings/notifications page renders preference matrix
- [ ] Toggle switches for each notification_type x channel combination
- [ ] Save button calls PUT /notification-preferences
- [ ] Loading, success, and error states handled
- [ ] 10 component tests passing

## Approach
Create frontend/src/app/admin/settings/notifications/page.tsx with:
- Fetch preferences on mount via api.get()
- Render 8 notification types × 2 channels as toggle matrix
- Save all preferences via api.put() on button click
