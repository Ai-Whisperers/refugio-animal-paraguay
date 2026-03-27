---
story: S2
epic: EPIC-88
ticket: RAP-597
title: "Responsive design audit and fixes"
status: ready
points: 6
priority: P0
track: Frontend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S02: Mobile-First Responsive Audit and Fixes

## Story

As a mobile user, I want all pages of the Refugio Animal Paraguay website to work perfectly on my smartphone without horizontal scrolling or tiny text so that I can easily browse and interact with the platform.

## Description

Comprehensive responsive design audit of all 12 public pages on 375px viewport (iPhone SE size). Identify and fix all responsive issues including touch target sizes, font sizes, horizontal scroll, hamburger menu functionality, form zoom behavior, image loading optimization, and Core Web Vitals optimization.

## Acceptance Criteria

- [ ] Audit all 12 public pages: home, animals list, animal detail, adoption application, contact, about, campaigns, blog, events, donate, login, register
- [ ] Verify all interactive elements have minimum touch target size of 44x44px (per WCAG 2.1)
- [ ] Fix any buttons, links, checkboxes smaller than 44x44px
- [ ] Audit all text on 375px viewport
- [ ] Ensure minimum font size of 16px for body text throughout all pages
- [ ] Verify no horizontal scrolling on any page at 375px viewport
- [ ] Test hamburger menu (if present) functions smoothly with touch
- [ ] Verify menu items are selectable and readable on 375px
- [ ] Audit all form inputs on adoption application form
- [ ] Add explicit font-size >= 16px to all input, select, textarea elements to prevent iOS zoom on focus
- [ ] Verify form inputs don't cause page zoom when user focuses on them
- [ ] Implement lazy loading (loading="lazy" or IntersectionObserver) for all images
- [ ] Verify images have appropriate responsive sizes using srcset or picture elements
- [ ] Test Largest Contentful Paint (LCP) metric: target under 2.5s on 4G mobile connection
- [ ] Test Cumulative Layout Shift (CLS): target under 0.1
- [ ] Test First Input Delay (FID): target under 100ms
- [ ] Run Lighthouse performance audit on all pages: target score >90 on mobile
- [ ] Fix critical accessibility issues found in audit
- [ ] Test on actual iOS and Android devices at 375px resolution

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] CSS media queries and responsive layout verified
- [ ] Unit tests for responsive image components
- [ ] Manual testing on Chrome DevTools mobile emulation
- [ ] Manual testing on actual iPhone SE or equivalent (375px)
- [ ] Manual testing on actual Android phone at 375px (e.g., Pixel 4a)
- [ ] Lighthouse PWA score >90 on all pages
- [ ] Core Web Vitals green across all public pages
- [ ] Performance budget: <200KB first load JS, <100KB critical CSS
- [ ] Documentation: list of responsive design fixes made
- [ ] Deployed to staging and verified

## Technical Notes

- Use mobile-first CSS approach: base styles for mobile, media queries for larger screens
- Test at 375px (iPhone SE), 414px (iPhone 12), 768px (iPad) breakpoints
- Use Chrome DevTools device emulation to test responsive behavior
- Verify font loading doesn't block rendering (use font-display: swap)
- Optimize images: serve WebP with PNG fallback, use next/image if available
- Test hamburger menu interaction with both touch and keyboard navigation
- Verify form labels are associated with inputs (for accessibility)
- Use relative units (rem, em) instead of fixed pixels for better scaling

## Story Points: 8
