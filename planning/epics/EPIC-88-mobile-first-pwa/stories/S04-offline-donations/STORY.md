---
story: S4
epic: EPIC-88
ticket: RAP-599
title: "Offline donation forms with IndexedDB"
status: ready
points: 6
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S04: Offline Donation Form

## Story

As a donor, I want to fill out and submit the donation form even if my internet connection drops so that I can complete my donation when connectivity is restored.

## Description

Implement offline-first donation form that saves submission to IndexedDB when network is unavailable, automatically retries submission when connection is restored, and provides clear feedback about queued donations.

## Acceptance Criteria

- [ ] Detect network availability using navigator.onLine and online/offline events
- [ ] Donation form (/donate) works completely offline: user can fill all fields
- [ ] Form submit button is always enabled (no greyed out when offline)
- [ ] If network unavailable on submit: save form data to IndexedDB instead of HTTP request
- [ ] Display message: "Donacion guardada sin conexion - se enviara cuando haya conexion" (Donation saved offline - will send when connected)
- [ ] Create IndexedDB database "refugio" with object store "queuedDonations"
- [ ] Queue schema: {id, amount, currency, name, email, message, timestamp, retries}
- [ ] Store maximum 5 queued donations
- [ ] When 6th donation attempted: show message "Maximo 5 donaciones en cola" (Maximum 5 donations queued)
- [ ] Show "Conexion restaurada" toast when network comes back online
- [ ] Auto-submit queued donations one-by-one when network available
- [ ] Retry failed donations up to 3 times with exponential backoff (1s, 2s, 4s)
- [ ] After successful submission: remove from queue and show success message
- [ ] If all retries fail: keep in queue and show message "Reintentando..." (Retrying...)
- [ ] Display count of queued donations: "X donaciones pendientes" (X donations pending)
- [ ] Allow user to view list of queued donations
- [ ] Allow user to delete/cancel individual queued donations
- [ ] Clear queued donations after successful submission
- [ ] Test offline/online transitions
- [ ] Test on iOS Safari and Android Chrome

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] IndexedDB implementation verified
- [ ] Offline form persistence tested
- [ ] Auto-submit on reconnect verified
- [ ] Retry logic tested with failure scenarios
- [ ] Unit tests for queue management, retry logic
- [ ] Integration test for offline to online workflow
- [ ] Manual testing on mobile browsers
- [ ] Manual testing of network toggle (Chrome DevTools offline mode)
- [ ] Error handling for quota exceeded
- [ ] UI/messaging verified for clarity
- [ ] Deployed to staging and verified

## Technical Notes

- Use IndexedDB API for persistent offline storage (better than localStorage for large data)
- Implement service worker to intercept donation POST requests
- Use exponential backoff for retries: 1000ms, 2000ms, 4000ms
- Handle network switch with online/offline event listeners
- Verify IndexedDB transaction handling
- Test on low-end devices with small storage quota
- Consider cleanup: delete queued items after 7 days of failed retries
- Implement clear error messages for storage quota exceeded

## Story Points: 5
