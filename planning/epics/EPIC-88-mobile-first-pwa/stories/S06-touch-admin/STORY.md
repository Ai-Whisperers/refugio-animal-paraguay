---
story: S6
epic: EPIC-88
ticket: RAP-601
title: "Touch-friendly admin interface"
status: ready
points: 4
priority: P0
track: Frontend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S06: Touch-Friendly Admin Interface

## Story

As a staff member working in the field, I want the admin interface to work smoothly on my mobile device so that I can manage animals and applications from anywhere.

## Description

Optimize admin interface for mobile touch interaction. Implement swipeable drawer navigation, horizontal scroll with sticky first columns for tables, bottom action bars for mobile, and full-screen modal dialogs on small screens.

## Acceptance Criteria

- [ ] Admin sidebar: convert to swipeable drawer on mobile (<768px)
- [ ] Drawer toggles with hamburger menu button on mobile
- [ ] Swipe from left edge opens drawer, swipe right or click overlay closes it
- [ ] Drawer content fully readable and scrollable
- [ ] All admin data tables have horizontal scroll capability
- [ ] First column (name/ID) remains sticky (position: sticky) while scrolling horizontally
- [ ] Scrollbar visible and usable on mobile
- [ ] Table action buttons (edit, delete, approve) moved to bottom action bar on mobile
- [ ] Bottom action bar appears only when table row selected
- [ ] Action buttons in bottom bar: minimum 50px height for touch
- [ ] Modal dialogs: full-screen on mobile (<768px), centered modal on desktop
- [ ] Modal close button prominent (top-right corner, min 44x44px)
- [ ] Modal content scrolls independently if exceeds screen height
- [ ] Date picker inputs: use native mobile date picker (input type="date")
- [ ] Select/dropdown: use native mobile select on mobile
- [ ] Form inputs: minimum 44px height for touch targets
- [ ] Remove hover-dependent interactions (buttons that only appear on hover)
- [ ] Test all touch interactions: tap, long-press, swipe
- [ ] Verify no JavaScript errors on mobile
- [ ] Test on 375px viewport (iPhone SE)
- [ ] Test on 414px viewport (iPhone 12)

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Responsive layout implemented with CSS media queries
- [ ] Drawer navigation with smooth animations
- [ ] Table horizontal scroll with sticky columns tested
- [ ] Bottom action bar functionality tested
- [ ] Modal responsive behavior verified
- [ ] Unit tests for drawer open/close
- [ ] Integration test for table actions on mobile
- [ ] Manual testing on actual iOS device
- [ ] Manual testing on actual Android device
- [ ] Touch interaction testing: no lag or janky animations
- [ ] Performance verified: smooth scrolling, no dropped frames
- [ ] Accessibility: touch targets meet WCAG 2.1 AAA (min 56x56px)
- [ ] Deployed to staging and verified

## Technical Notes

- Use CSS media queries: @media (max-width: 768px)
- Implement drawer with CSS transform for smooth animation
- Use position: sticky for table first column (check browser support)
- Hide hover-only elements on touch devices using @media (hover: none)
- Test with actual touch input, not mouse emulation
- Ensure bottom action bar doesn't cover content
- Use CSS Grid or Flexbox for responsive layout
- Test drawer swipe gesture with touch-action property if using custom gesture
- Verify no input zoom-on-focus behavior (font-size >= 16px on inputs)

## Story Points: 5
