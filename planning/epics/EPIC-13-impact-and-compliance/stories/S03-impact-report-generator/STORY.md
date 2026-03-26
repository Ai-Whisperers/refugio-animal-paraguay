---
story: S03
epic: EPIC-13
title: Impact Report Generator
status: ready
created: 2026-03-26T00:00:00.000000
effort: 7
---

# S03: Impact Report Generator

## User Story

As a **shelter director or fundraiser**, I want to **auto-generate quarterly and annual impact reports as PDFs** so that **I can share quantified shelter outcomes with donors, funders, and stakeholders without manual compilation**.

## Acceptance Criteria

**Given** I am a staff member with reporting permissions
**When** I request an impact report for a date range
**Then** the system generates a PDF with all impact metrics and visualizations

**Given** a report is generated
**When** I open it
**Then** it includes: animals served, adoptions (by species), donations (total and by currency), fund allocation breakdown, cost-per-adoption, average time-to-adoption

**Given** I am reviewing a quarterly report
**When** I view the report
**Then** I see trend comparisons (this quarter vs. last quarter) and year-over-year metrics

**Given** the report is prepared
**When** I export it
**Then** the PDF is branded with the shelter logo and includes a summary narrative section I can edit

**Given** an impact report is generated
**When** staff reviews it
**Then** all metrics are accurate to the underlying database (no manual entry errors)

## Tasks

- T01: Design and implement impact report schema and data aggregation queries
- T02: Build report generator service that queries database and calculates metrics
- T03: Create PDF template and rendering service (using a library like ReportLab or WeasyPrint)
- T04: Implement staff interface to request and download reports
- T05: Add report scheduling (auto-generate monthly/quarterly/annual reports)

## Definition of Done

- [ ] Report metrics correctly calculated: animals served, adoptions, donations, fund allocation
- [ ] PDF includes visuals: bar charts for adoption by species, pie charts for fund allocation, line charts for trends
- [ ] Report generation completes in < 5 seconds for 1-year data range
- [ ] Generated PDFs are consistently formatted with shelter branding
- [ ] Trend comparisons displayed accurately (quarter-over-quarter, year-over-year)
- [ ] Unit tests cover metric calculations (85%+ coverage)
- [ ] Integration tests verify full report generation for sample data
- [ ] No sensitive personal data included in reports (only aggregated metrics)

## Technical Notes

- Report metrics: total_animals_served, adoptions_count (by species), total_donations, donations_by_currency, fund_allocation (by category), cost_per_adoption, avg_time_to_adoption_days, foster_placements, volunteer_hours
- Report data model: start_date, end_date, generated_date, generated_by_user_id, report_type (quarterly, annual, custom), metrics (JSON), narrative (text)
- PDF generation: use ReportLab or WeasyPrint with template for consistent styling
- Scheduling: use Celery or APScheduler to generate standard reports on schedule
- Optional: add ability to compare two date ranges side-by-side
- Archive: store generated reports in database for historical access

## Dependencies

- Depends on: EPIC-1 (Animal records for adoption counts)
- Depends on: EPIC-3 (Donation data and fund allocation)
- Depends on: S04-fund-allocation-tracking (fund allocation breakdown)
- Blocks: EPIC-14 (Campaign reporting uses impact data)

## Story Points: 7
