---
story: S5
epic: EPIC-86
ticket: RAP-584
title: "Simplified 1-click donation for emergencies"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 14
version: V1
created: 2026-03-27T20:00:00
---

# S5: Simplified 1-click donation for emergencies

## Story
As a **supporter**, I want **to donate quickly to emergencies** so that **help reaches animals fast**.

## Description
Create simplified donation page for emergencies. Logged-in users with saved payment see 1-click donate. Guests see minimal form. Pre-filled suggested amounts.

## Acceptance Criteria
- [ ] /emergencies/{id}/donate page accessible to all users
- [ ] Page layout: large emergency header (photo, title, amount needed), donation amount selector, submit button
- [ ] Suggested amounts: buttons showing 10%, 25%, 50%, 100% of remaining_needed, or fixed: $50, $100, $250, $500
- [ ] Custom amount input: text field to enter any amount, currency selector (USD, PYG)
- [ ] For logged-in users with saved payment method: show "Quick Donate" option
- [ ] Quick Donate: single click confirms and charges (with confirmation dialog)
- [ ] For logged-in users without saved payment: show payment form (existing donation form)
- [ ] For guests: simplified form with email, amount, currency, payment method (Stripe, etc)
- [ ] Form validation: amount > 0, email valid for guests
- [ ] Submit button text: "Donate [Amount]" with currency
- [ ] Success page: "Thank you for helping [animal]!" with donation confirmation
- [ ] Show impact message: "You've helped reach [X]% of the goal!"
- [ ] Share button: "Share this emergency" with pre-filled message
- [ ] Mobile responsive: full-width inputs, large donation buttons
- [ ] Accessibility: proper labels, clear form structure

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: donate as logged-in user, as guest
- [ ] E2E test: quick donate flow end-to-end
- [ ] Payment processing tested (use test/sandbox mode)
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] Deployed to staging and verified

## Technical Notes
- Reuse existing donation payment integration
- Pre-fill amounts based on remaining needed
- Show progress toward goal after donation
- Consider adding social proof: "X people have donated"
- Track donation source: emergency vs campaign vs direct

## Story Points: 5
