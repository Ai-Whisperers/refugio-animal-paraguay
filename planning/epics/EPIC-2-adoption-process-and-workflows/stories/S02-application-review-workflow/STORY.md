---
story: S02
epic: EPIC-2
title: Application Review Workflow
status: ready
created: 2026-03-25T17:13:26.727790
version: V1
---

# S02: Application Review Workflow

## Description

Staff/admin dashboard for reviewing pending adoption applications, approving/rejecting with notes, and tracking application status.

## Acceptance Criteria

**Given** I am a staff member with review permissions
**When** I access the admin dashboard → Adoption Applications
**Then** I see a list of pending applications sorted by submission date, showing applicant name, animal name, submission date, and review status

**Given** I click on a pending application
**When** the application details load
**Then** I see all submitted information (applicant details, household info, experience, animal preferences) in a readable format with scrollable sections

**Given** I review an application
**When** I decide to approve it
**Then** I click "Approve", optionally add approval notes, and confirm — the application status changes to approved and applicant receives approval email

**Given** I review an application and want to reject it
**When** I click "Reject"
**Then** a modal appears requiring me to enter a rejection reason, I submit, and the applicant receives rejection email with reason

**Given** multiple applications exist
**When** I filter the applications list
**Then** I can filter by status (pending, approved, rejected), animal name, or date range to find specific applications

**Given** an application is in progress
**When** I view the application list
**Then** applications show a status badge (pending=yellow, approved=green, rejected=red) and pending count is displayed prominently

**Given** I have approved an application
**When** the approval is recorded
**Then** the application becomes eligible for contract generation and adoption finalization (triggering next workflow step)

## Tasks

- T01: Create review dashboard
- T02: Implement approval/rejection logic
