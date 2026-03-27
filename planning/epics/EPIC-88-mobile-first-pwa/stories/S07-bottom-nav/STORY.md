---
story: S7
epic: EPIC-88
ticket: RAP-602
title: "App-like bottom navigation bar"
status: ready
points: 4
priority: P0
track: Frontend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S07: App-Like Navigation with Bottom Tab Bar

## Story

As a mobile user browsing the public website, I want a bottom navigation bar like a native app so that I can easily switch between main sections without scrolling to the top.

## Description

Implement bottom navigation tab bar for mobile public pages with 5 main tabs: Home, Animals, Donate, Community, Profile. Add visual feedback for active tab, notification badges, and smart show/hide behavior that reveals on scroll up and hides on scroll down.

## Acceptance Criteria

- [ ] Add bottom navigation bar on mobile (<768px) public pages only
- [ ] Bottom nav NOT on admin pages (keep sidebar navigation for admin)
- [ ] 5 tabs in bottom nav: Home, Animals, Donate, Community, Profile
- [ ] Each tab with icon and label
- [ ] Tab icons: Home, Animals/Paw, Heart/Donate, Users/Community, User/Profile
- [ ] Active tab highlighted with theme color (#1B4F72 or primary color)
- [ ] Active tab icon filled, inactive icons outlined
- [ ] Tab label text color matches icon color (active vs inactive)
- [ ] Each tab is 20% width (5 equal columns)
- [ ] All touch targets minimum 44x44px
- [ ] Notification badge on Community tab if new messages/posts
- [ ] Notification badge on Profile tab if pending notifications
- [ ] Badge shows count: "3" (maximum 2 chars)
- [ ] Bottom nav sticky to bottom of viewport: position fixed/sticky
- [ ] Background color: white or light background with shadow
- [ ] Page content scrolls behind/under bottom nav (not pushed up)
- [ ] On scroll down: smoothly hide bottom nav over 300ms
- [ ] On scroll up: smoothly show bottom nav over 300ms
- [ ] Tab clicks navigate to: /, /animals, /donate, /community, /portal/profile
- [ ] Active tab indicator updates as user navigates
- [ ] Test scroll behavior is smooth and responsive
- [ ] Test on 375px, 414px viewport

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Bottom navigation component created
- [ ] Tab routing/navigation working
- [ ] Active state tracking and styling
- [ ] Scroll-based show/hide animation
- [ ] Notification badge display logic
- [ ] Unit tests for active tab tracking
- [ ] Integration test for tab navigation
- [ ] Manual testing on actual iOS device
- [ ] Manual testing on actual Android device
- [ ] Scroll animation smooth and performant
- [ ] Touch interactions responsive
- [ ] No overlap with page content in footer area
- [ ] Deployed to staging and verified

## Technical Notes

- Use position: fixed with bottom: 0, width: 100%
- Use CSS transform for smooth show/hide: translateY(0) vs translateY(100%)
- Debounce scroll events to prevent excessive animation triggers
- Use React Router or next/router for tab navigation
- Track scroll direction: detect scrollY increasing (down) vs decreasing (up)
- Implement z-index to keep bottom nav on top of content
- Test scroll performance on low-end devices
- Use CSS transitions or framer-motion for smooth animations

## Story Points: 3
