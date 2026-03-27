---
story: S3
epic: EPIC-86
ticket: RAP-582
title: "Emergency featured on homepage"
status: ready
points: 5
priority: P0
track: Frontend
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S3: Emergency featured on homepage

## Story
As a **visitor**, I want **to see urgent emergencies on homepage** so that **I can help immediately**.

## Description
Homepage displays prominent banner when active emergencies exist. Red/orange styling with pulsing indicator. Shows single highest-urgency emergency with donate button.

## Acceptance Criteria
- [ ] GET /api/emergencies/active endpoint returns active emergencies ordered by urgency (critical first) then created_at DESC
- [ ] Homepage checks for active emergencies on mount
- [ ] If emergencies exist: display EMERGENCY banner at top of page (above nav on mobile, below nav on desktop)
- [ ] Banner styling: red/orange background, white text, pulsing red dot icon (CSS animation)
- [ ] Banner content: "EMERGENCY: [Title]" with featured photo, amount needed vs raised, time remaining
- [ ] Banner shows single highest-urgency emergency only
- [ ] Banner includes large "DONATE NOW" button (primary CTA)
- [ ] Click button navigates to /emergencies/{id}/donate (S5 simplified donation)
- [ ] Time remaining displayed: "36 hours remaining" format, updates without page refresh (or show deadline date)
- [ ] Progress bar shows amount_raised / amount_needed with percentage
- [ ] Photo is primary animal photo or first emergency photo
- [ ] If no active emergencies: banner doesn't show (empty state)
- [ ] Banner dismissible: small X button closes it for current session (stored in localStorage)
- [ ] Re-appear on page refresh or next visit
- [ ] Mobile responsive: banner full-width, button full-width on mobile
- [ ] Accessibility: banner marked as region with aria-live="polite", button accessible

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: create emergency, verify appears on homepage
- [ ] E2E test: visit homepage, see emergency banner
- [ ] Animations tested across browsers
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] Deployed to staging and verified

## Technical Notes
- Fetch emergencies on app boot or every 1 minute
- Use CSS keyframes for pulsing animation
- Cache for 1 minute (trade-off between freshness and performance)
- Consider confetti or celebration effect when emergency becomes funded

## Story Points: 5
