---
story: S8
epic: EPIC-80
ticket: RAP-540
title: "Rescuer verification system"
status: ready
points: 3
priority: P2
track: Backend
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S8: Rescuer verification system

## Story
As a **platform**, I want **to verify rescuers** so that **donors trust they're supporting legitimate efforts**.

## Description
Implement multi-method verification: WhatsApp phone verification, social media link verification, time-based trust.

## Acceptance Criteria
- [ ] Verification methods: WhatsApp phone verification (reuse from EPIC-76 S6), social media link verification, time-based (verified after 30 days activity + 5 animals listed)
- [ ] WhatsApp verification: send OTP via WhatsApp, rescuer verifies phone
- [ ] Social media verification: admin checks social media links (Facebook, Instagram) for authenticity
- [ ] Time-based verification: auto-verify if: 30+ days since registration AND 5+ animals listed AND positive donor feedback
- [ ] Admin verification: admin can manually verify or unverify rescuers with reason
- [ ] Verified badge: shows on profile when is_verified=true
- [ ] Unverified restrictions: unverified rescuers' campaigns require approval before publishing
- [ ] Appeals: rescuers can request verification with documentation

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test: WhatsApp verification works
- [ ] Integration test: time-based auto-verification triggers
- [ ] Integration test: admin verification works
- [ ] Deployed to staging and verified

## Technical Notes
- Verification model: stores verification_method, verified_at, verified_by (admin_id)
- Auto-verification: cron job daily checks for time-based requirements
- Admin interface: /admin/rescuers shows unverified list with verify button
- WhatsApp: reuse from EPIC-76 S6 implementation

## Story Points: 3
