---
story: S02
epic: EPIC-13
title: GDPR Data Export
status: ready
created: 2026-03-26T00:00:00.000000
effort: 6
version: V3
---

# S02: GDPR Data Export

## User Story

As a **data subject (donor, adopter, or staff member)**, I want to **request and download my personal data in a portable format (GDPR Articles 15 & 20)** so that **I can exercise my right to access and data portability, and migrate my data to another organization**.

## Acceptance Criteria

**Given** I am a registered donor/adopter/staff member
**When** I access my account settings
**Then** I see a "Request My Data Export" button in the Data & Privacy section

**Given** I request a data export
**When** the request is submitted
**Then** the system logs the request with timestamp, request ID, and data subject identity for audit trail compliance

**Given** my data export is processed by the system
**When** the export is ready
**Then** I receive an email with a secure download link (valid for 7 days) containing a JSON file with all my personal data

**Given** I download my exported data
**When** the file is received
**Then** the JSON includes: profile (name, email, address, phone), donation history (amount, date, currency, tax receipt status), adoption records (animal name, date, status), communication preferences, and activity audit trail

**Given** I request an export as a staff member
**When** the export is generated
**Then** the file also includes my volunteer/shift history, task assignments, and role/permission records

**Given** my data export contains sensitive information
**When** the download link is accessed
**Then** the download is tracked in the audit log and the link becomes inactive after one download

**Given** I did not download my exported data within 7 days
**When** the expiration deadline passes
**Then** the temporary export file is securely deleted and I must request a new export

## Tasks

- T01: Implement POST /api/gdpr/data-export request endpoint (validation, audit logging)
- T02: Build background job for data aggregation and JSON serialization
- T03: Implement secure download link generation and expiration tracking
- T04: Add "Request My Data Export" UI in user account settings
- T05: Email notification service for export ready/link expiration
- T06: Unit tests for data filtering and JSON serialization (90%+ coverage)
- T07: Integration tests for full export request → download lifecycle
- T08: Security tests for download link validation and replay attack prevention

## Definition of Done

- [ ] Data export endpoint returns all personal data fields per spec
- [ ] Export format is valid JSON, schema-documented
- [ ] Download links expire correctly and are not reusable
- [ ] Audit trail records all data export requests
- [ ] No unencrypted personal data in logs or error messages
- [ ] Email notifications sent reliably with link and expiration info
- [ ] Unit test coverage ≥90% for export logic
- [ ] Integration tests cover happy path and error scenarios
- [ ] Deployed to staging and verified

## Technical Notes

- Export schema: user_id, export_date, export_uuid (unique request ID), data_subjects array with profile, donations, adoptions, communications, audit_entries
- Donation data: amount (EUR/PYG), date, frequency (one-time/recurring), payment method, tax receipt status, fund allocation
- Secure download: generate JWT token with exp claim (7 days), single-use tracking in download_tokens table
- Background job: triggered immediately on request, runs async, sends email on completion or failure
- Encryption: exports at rest in temp storage (encrypted with data key from KMS), deleted after 7 days
- Consider: support for batch export requests (export all data across multiple accounts user owns)

## Dependencies

- Depends on: S01-audit-trail-system (export requests must be logged)
- Depends on: EPIC-10 (User authentication and account management)
- Blocks: S06-gdpr-data-deletion (deletion should reference export requests)

## Story Points: 6
