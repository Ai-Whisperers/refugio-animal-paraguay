---
story: S9
epic: EPIC-80
ticket: RAP-541
title: "Admin moderation tools"
status: done
points: 5
priority: P2
track: Fullstack
sprint: 13
version: V1
created: 2026-03-27T20:00:00
---

# S9: Admin moderation tools

## Story
As an **admin**, I want **to moderate rescuer content** so that **we maintain platform quality and trust**.

## Description
Create admin moderation tools to manage rescuer profiles, campaigns, and content.

## Acceptance Criteria
- [ ] /admin/rescuers page: list all rescuers with: name, status, verification status, animal count, supporter count, flags
- [ ] Rescuer actions: verify/unverify (with reason), suspend/unsuspend (blocks posting), flag for review
- [ ] Campaign moderation: /admin/campaigns shows pending/unverified rescuer campaigns with approve/reject buttons
- [ ] Content flagging: users can flag inappropriate content, flagged items appear in /admin/flags dashboard
- [ ] Flag review: admin can review flags, dismiss or take action (remove, suspend rescuer, contact rescuer)
- [ ] Search/filter: search rescuers by name, filter by status (verified, unverified, suspended, flagged)
- [ ] Bulk actions: select multiple rescuers to verify/suspend in bulk
- [ ] Moderation history: view all mod actions with timestamp and reason

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Component test: moderation interface renders
- [ ] Integration test: verify/suspend actions work
- [ ] Integration test: flags displayed
- [ ] Deployed to staging and verified

## Technical Notes
- ModerationLog table: tracks all admin actions
- Flags table: user_id, content_type, content_id, reason, status, created_at
- Bulk actions: batch update queries
- UI: list view with actions per row, filter/search sidebar

## Story Points: 5
