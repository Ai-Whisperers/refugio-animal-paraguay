---
story: S1
epic: EPIC-88
ticket: RAP-596
title: "PWA manifest and service worker setup"
status: ready
points: 5
priority: P0
track: Frontend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S01: PWA Manifest and Service Worker Setup

## Story

As a mobile user, I want the Refugio Animal Paraguay website to be installable as an app on my home screen so that I can access it quickly like a native application.

## Description

Implement the foundational PWA infrastructure including manifest.json configuration with proper metadata, service worker registration and setup for offline support, and offline fallback page for when network is unavailable. This establishes the base PWA capabilities that all other mobile features build upon.

## Acceptance Criteria

- [ ] Add manifest.json at public/manifest.json with: name "Refugio Animal Paraguay", short_name "Refugio", theme_color "#1B4F72", background_color "#ffffff", display "standalone", icons array with 192x192px and 512x512px PNG files
- [ ] Link manifest in HTML head with <link rel="manifest" href="/manifest.json">
- [ ] Register service worker via JavaScript at app initialization using navigator.serviceWorker.register('/sw.js')
- [ ] Service worker file (public/sw.js) successfully installs and activates
- [ ] Service worker caches critical assets on install: HTML shell, CSS, JavaScript bundles, core images, fonts
- [ ] Create offline fallback page at public/offline.html showing message "Sin conexion - intenta de nuevo" (No connection - try again)
- [ ] Service worker intercepts failed network requests and serves offline.html for navigation requests
- [ ] Install prompt appears on mobile browsers after first visit completes and user returns within 2 days
- [ ] Install prompt displays correctly with app icon, name "Refugio Animal Paraguay", and install button
- [ ] Successfully installed PWA appears on home screen with correct icon
- [ ] PWA icon in Android app drawer reflects theme_color setting
- [ ] Lighthouse PWA audit scores minimum 80 on PWA installability and service worker criteria

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Unit tests for service worker lifecycle (install, activate, fetch)
- [ ] Integration test for offline fallback rendering
- [ ] Cross-browser testing: Chrome, Firefox, Safari on iOS 13+, Samsung Internet
- [ ] Manual testing on actual Android and iOS devices
- [ ] Lighthouse PWA audit run and documented
- [ ] Performance impact measured (install size, load time overhead)
- [ ] Documentation updated with manifest configuration details
- [ ] Deployed to staging and verified on mobile

## Technical Notes

- Use Workbox library for service worker if available, or implement custom service worker
- Cache strategy: on-install for critical assets, on-demand for images
- Include cache version in service worker to manage updates
- Verify manifest.json valid with manifest validator
- Test offline page on 375px viewport for responsiveness
- Ensure service worker compatibility with browsers supporting ES5+ syntax
- Configure cache expiration for assets (update monthly)

## Story Points: 5
