---
story: S06
epic: EPIC-13
title: GDPR Data Deletion
status: ready
created: 2026-03-26T00:00:00.000000
effort: 5
version: V3
---

# S06: GDPR Data Deletion

## User Story

As a **data subject (donor, adopter, or staff member)**, I want to **request the deletion of my personal data (GDPR Article 17 — right to erasure)** so that **my information is removed from the shelter system while the organization maintains accounting/donation records as legally required**.

## Acceptance Criteria

**Given** I am a registered user
**When** I access my account settings and initiate a deletion request
**Then** I see a confirmation dialog explaining that deletion is permanent and will remove my profile, adoption records, and communications

**Given** I confirm my deletion request
**When** the request is submitted
**Then** the system creates a GDPR deletion record (user_id, request_id, timestamp, reason if provided, status=pending) and sends a staff notification

**Given** a staff member reviews my deletion request
**When** they approve the deletion in the admin dashboard
**Then** the system executes the deletion while preserving donation records (anonymized as "Anonymous Donor")

**Given** my personal data is deleted from the system
**When** the deletion is executed
**Then** the following records are hard-deleted: user profile, contact information, adoption records (soft-deleted with anonymized adopter), communications history, personal volunteer records

**Given** a donor record exists with associated donations
**When** the donor is deleted
**Then** the donation amounts, dates, and tax receipt references are preserved in an "anonymous_donation" record with donor_id=NULL, but donor name/email/address are removed

**Given** a staff member or volunteer is deleted
**When** the deletion is executed
**Then** their shift history is anonymized (volunteer_id=NULL, hours preserved for reporting), task assignments are reassigned or archived, role records are deleted

**Given** a deletion request is approved and executed
**When** the process completes
**Then** both the user and staff receive confirmation emails, and the deletion is logged in the audit trail with staff approver and timestamp

**Given** a user requests their own deletion
**When** 30 days have passed since the request
**Then** if the request is not cancelled, the system auto-executes the deletion with a final warning email sent at day 25

## Tasks

- T01: Implement DELETE /api/gdpr/user/{user_id} deletion request endpoint (validation, audit logging)
- T02: Create staff dashboard UI for reviewing pending deletion requests with approve/deny buttons
- T03: Implement data anonymization logic for donations (donor_id=NULL, preserve amount/date/tax_id)
- T04: Implement hard delete operations for user profile, addresses, communications, adoption records
- T05: Soft delete/anonymization for volunteer records (preserve hours, shift history)
- T06: 30-day grace period tracking and auto-execution workflow with warning emails
- T07: Email notifications for deletion request confirmation, approval, and execution
- T08: Unit tests for anonymization logic and data integrity validation (90%+ coverage)
- T09: Integration tests for full deletion workflow including grace period and auto-execution

## Definition of Done

- [ ] Deletion request endpoint validates user identity and creates audit record
- [ ] Staff dashboard shows pending deletion requests with reason and request timestamp
- [ ] Donation records preserved (anonymized) while donor PII deleted
- [ ] Volunteer/shift records anonymized while hours preserved for reporting
- [ ] 30-day grace period enforced with warning emails at day 1 and day 25
- [ ] Audit trail logs all deletions with staff approver and timestamp
- [ ] No PII leaked in email notifications or error messages
- [ ] Unit test coverage ≥90% for deletion and anonymization logic
- [ ] Integration tests cover grace period, auto-execution, and error recovery
- [ ] Deployed to staging and verified with test data cleanup validation

## Technical Notes

- Deletion strategy:
  - Hard delete: user_account, donor_profile, adopter_profile, staff_profile, contact records, communications
  - Soft delete/anonymize: donations (create anonymous_donation record), volunteer_shifts (volunteer_id=NULL), task_assignments
- Grace period: 30 days before auto-execution; user can cancel anytime before execution
- Warning emails: immediate confirmation, day 25 final warning with "request cancellation" link, day 31 execution confirmation
- Anonymization: use trigger or service to update donation.donor_id=NULL, volunteer_shift.volunteer_id=NULL
- Audit table updates: log deletion request, approval, execution with staff_id, reason, timestamp
- Referential integrity: ensure no orphaned foreign keys after deletion; test all deletion scenarios

## Dependencies

- Depends on: S01-audit-trail-system (deletion requests and executions must be logged)
- Depends on: S02-gdpr-data-export (users may export before requesting deletion)
- Depends on: EPIC-10 (User authentication and account management)
- Blocks: S03-impact-report-generator (reports must account for anonymized/deleted donors)

## Story Points: 5
