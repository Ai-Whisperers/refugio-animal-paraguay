---
story: S7
epic: EPIC-85
ticket: RAP-579
title: "Campaign real-time progress"
status: ready
points: 3
priority: P2
track: Frontend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S7: Campaign real-time progress

## Story
As a **supporter**, I want **to see campaign progress update without refreshing** so that **I can see impact of donations in real-time**.

## Description
Campaign detail page updates progress bar and amount raised without requiring page refresh. Uses polling or SSE to fetch fresh data.

## Acceptance Criteria
- [ ] Campaign detail page progress bar updates every 30 seconds (configurable poll interval)
- [ ] Alternative: SSE stream for real-time updates if backend supports it
- [ ] When update received, progress bar smoothly animates to new percentage
- [ ] Amount raised updates: "[Current] of [Goal]"
- [ ] Progress percentage updates: "[X]%"
- [ ] Donation flash notification: "Donation just received!" appears momentarily when progress updates
- [ ] Flash notification positioned near progress bar with green checkmark icon
- [ ] If campaign becomes fully funded: progress bar turns blue, show "FULLY FUNDED!" badge
- [ ] If campaign over-funded: show "EXCEEDED! +[X] over goal"
- [ ] Poll only while user on page: stop polling if page hidden/unfocused (document.hidden API)
- [ ] Graceful degradation: if polling fails, show static progress (fallback to last known value)
- [ ] Mobile responsive: progress bar full width, text stacked
- [ ] Accessibility: ARIA live region announces progress updates, screen reader friendly

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: update campaign amounts, verify polling fetches new data
- [ ] E2E test: open campaign page, donate, verify progress updates within 30 seconds
- [ ] Polling behavior tested: stops when page unfocused, resumes when focused
- [ ] Animation tested across browsers
- [ ] Accessibility audit passed
- [ ] Performance verified: polling doesn't overwhelm server
- [ ] Deployed to staging and verified

## Technical Notes
- Use setInterval for polling, clear on component unmount
- Implement document.hidden check to pause polling
- Use ref or state to track last update (prevent unnecessary re-renders)
- Consider React Query for background polling with built-in management
- Animate progress bar with CSS transition or react-spring
- Log polling metrics for monitoring

## Story Points: 3
