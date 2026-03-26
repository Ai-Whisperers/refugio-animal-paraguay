---
story: S03
epic: EPIC-2
title: Adoption Notifications
status: ready
created: 2026-03-25T17:13:26.728107
version: V3
---

# S03: Adoption Notifications

## Description

Automated WhatsApp and email notifications for adoption application status updates, approvals, rejections, and next steps.

## Acceptance Criteria

**Given** an adopter submits an adoption application
**When** the submission is recorded
**Then** they receive an email confirmation with application reference number and expected review timeline

**Given** an adoption application is approved by staff
**When** the approval is recorded
**Then** the adopter receives both an email and WhatsApp message notifying them of approval with next steps (contract review, etc.)

**Given** an adoption application is rejected by staff
**When** the rejection is recorded
**Then** the adopter receives an email and WhatsApp with rejection reason and option to contact staff for feedback

**Given** an adopter has provided a phone number
**When** notifications are sent
**Then** WhatsApp messages are delivered to their phone number with clickable links to their account dashboard

**Given** an adopter receives multiple notifications
**When** they receive messages
**Then** each notification includes clear subject/title, status update, required action (if any), and support contact information

**Given** a notification message is sent
**When** the message is queued and delivered
**Then** a record is logged in the audit trail showing timestamp, recipient, message type, and delivery status

**Given** adoption application notifications are sent
**When** timing is tracked
**Then** email delivery occurs within 5 minutes, WhatsApp within 2 minutes of the triggering action

## Tasks

- T01: Setup WhatsApp API
- T02: Configure email notifications
