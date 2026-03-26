---
story: S04
epic: EPIC-7
title: Reporting & Export
status: ready
created: 2026-03-25T17:13:26.734532
version: V5
---

# S04: Reporting & Export

## Description

Comprehensive reporting and data export system supporting PDF, CSV, and Excel formats for operational and compliance reporting.

## Acceptance Criteria

**Given** I want to generate an adoption report
**When** I access Reports section
**Then** I see report templates: Adoption Summary, Donation Report, Volunteer Hours, Medical Summary, Animal Census

**Given** I select Adoption Summary report
**When** I configure report
**Then** I can set: date range, sort by (applicant/animal/date), and output format (PDF/CSV/Excel), then click Generate

**Given** a report is generated
**When** the report is ready
**Then** I can download file immediately and download link is also sent via email for archival

**Given** I generate a Donation Report
**When** report is configured (date range)
**Then** report shows: total donations, donations by method (Stripe/PayPal/Tigo), currency breakdown, donor names, and tax receipt status

**Given** I generate Volunteer Hours report
**When** I select date range and format
**Then** report shows: volunteer name, hours, roles, attendance rate, and monthly breakdown with totals

**Given** I need to export raw data
**When** I access Data Export
**Then** I can select: animals, adopters, donors, volunteers, donations, medical records and export all records in CSV or Excel with all fields

**Given** data is exported
**When** export completes
**Then** sensitive fields (passwords, payment tokens) are excluded, and export file is encrypted and expires in 7 days

**Given** I generate multiple reports
**When** I view my reports
**Then** I see a list of recent reports with generation date, filename, and option to re-download or delete

## Tasks

- T01: Implement report generator
- T02: Add export functionality
