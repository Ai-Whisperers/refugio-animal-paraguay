---
story: S8
epic: EPIC-89
ticket: RAP-611
title: "Expense approval workflow"
status: ready
points: 2
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S08: Expense Approval Workflow

## Story

As an administrator, I want larger expenses to require approval before they impact financial reports so that I can maintain oversight of significant spending.

## Description

Implement expense approval workflow where expenses above a configurable threshold require admin approval before appearing in public financial reports. Send notifications to admins when large expenses submitted.

## Acceptance Criteria

- [ ] Configure approval threshold in settings: default 500000 PYG / 100 EUR equivalent
- [ ] Make threshold configurable in admin settings page
- [ ] When expense created: check if amount > threshold
- [ ] If amount > threshold: set status to "pending" (requires approval)
- [ ] If amount <= threshold: set status to "auto_approved"
- [ ] Send notification to all admins when large expense submitted:
  - [ ] Email: "Nueva solicitud de aprobacion de gasto" (New expense approval request)
  - [ ] Include: expense amount, category, description, requester name
  - [ ] Include link: /admin/expenses/{id}
- [ ] Admin receives notification when:
  - [ ] Expense submitted (email)
  - [ ] Expense updated (email)
  - [ ] Expense rejected by another admin (email)
- [ ] Notification email in Spanish
- [ ] Notification includes "Aprobar" and "Rechazar" action buttons or links
- [ ] Admin can approve/reject directly from email link (one-click approval)
- [ ] Approval requires admin role (prevent escalation)
- [ ] Track who approved: approved_by user_id, approved_at timestamp
- [ ] Track who rejected: rejected_at timestamp, rejection_reason
- [ ] Rejected expenses remain in database (for audit), status="rejected"
- [ ] Only approved expenses appear in financial dashboard
- [ ] Query optimization: filter by status in financial calculations
- [ ] Notification delivery: max 5 minute delay after expense created
- [ ] Admin can bulk approve multiple pending expenses

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Threshold configuration working
- [ ] Notification system implemented
- [ ] Approval/rejection logic tested
- [ ] Financial dashboard filters tested
- [ ] Unit tests for threshold checking
- [ ] Integration tests for notification workflow
- [ ] Email delivery tested with real mailbox
- [ ] One-click approval links verified
- [ ] Bulk approval tested
- [ ] Manual end-to-end workflow testing
- [ ] Performance verified: queries still fast with status filter
- [ ] Deployed to staging and verified

## Technical Notes

- Store threshold in settings table
- Implement notification queue for reliable delivery
- Use one-time tokens for one-click approval links
- Implement audit log: track all approval/rejection actions
- Consider approval delegation: allow one admin to approve on behalf of another
- Implement escalation: if pending >5 days, send reminder
- Cache settings to avoid frequent database queries

## Story Points: 3
