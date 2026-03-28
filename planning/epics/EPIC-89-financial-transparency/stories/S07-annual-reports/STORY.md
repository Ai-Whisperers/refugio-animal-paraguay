---
story: S7
epic: EPIC-89
ticket: RAP-610
title: "Annual financial report generation"
status: done
points: 3
priority: P0
track: Backend
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S07: Annual Financial Report Generator

## Story

As an administrator, I want to generate comprehensive annual financial reports for audit and donor communication so that I can demonstrate financial accountability to stakeholders.

## Description

Create admin interface at /admin/reports/annual to generate and export comprehensive financial reports. Support PDF and CSV formats with detailed breakdowns of income, expenses, outcomes, and efficiency metrics.

## Acceptance Criteria

- [ ] Create /admin/reports/annual page
- [ ] Form to select report year (dropdown: current year, previous years)
- [ ] Generate report button: "Generar Reporte" (Generate Report)
- [ ] Report includes:
  - [ ] Executive summary: total income, total expenses, net result
  - [ ] Income breakdown: total donations by source (campaigns, general, etc.)
  - [ ] Expense breakdown: total by category with amounts and percentages
  - [ ] Expense detail: list of all approved expenses
  - [ ] Donor metrics: donor count, new donors, recurring donors, average donation
  - [ ] Animal outcomes: rescued (count), adopted (count), castrated (count), treated (count)
  - [ ] Financial efficiency: percentage of donations spent on direct care vs admin
  - [ ] Monthly breakdown: revenue and expenses by month
  - [ ] Campaign summaries: top 10 campaigns by donations
- [ ] PDF export format:
  - [ ] Professional formatted report with charts
  - [ ] Branded header with Refugio logo
  - [ ] Multiple pages with clear sections
  - [ ] Include charts: pie charts, bar charts, line graphs
- [ ] CSV export format:
  - [ ] One sheet: summary metrics
  - [ ] One sheet: detailed expenses
  - [ ] One sheet: monthly breakdown
  - [ ] One sheet: campaign summary
- [ ] Report generation time: <30 seconds for PDF
- [ ] Include report date and generation timestamp
- [ ] Add "Certified accurate by [Admin Name]" signature line
- [ ] Display before/after year comparison if previous year available
- [ ] Email report option: send to board members
- [ ] Archive reports: store generated reports for audit trail

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Report generation logic tested
- [ ] PDF generation working with proper formatting
- [ ] CSV export working with correct data
- [ ] Report accuracy verified against database
- [ ] Charts display correctly in PDF
- [ ] Performance tested: report generation <30s
- [ ] Unit tests for report calculations
- [ ] Integration tests for full report workflow
- [ ] Manual testing of PDF and CSV downloads
- [ ] Email delivery tested
- [ ] Archive storage verified
- [ ] Deployed to staging and verified

## Technical Notes

- Use ReportLab or similar for PDF generation
- Use csv module for CSV export
- Pre-aggregate data nightly for faster report generation
- Cache calculations in database
- Implement query optimization for large reports
- Consider using S3 for report storage and archival
- Generate sample data for testing
- Document calculation methodology in report footer

## Story Points: 5
