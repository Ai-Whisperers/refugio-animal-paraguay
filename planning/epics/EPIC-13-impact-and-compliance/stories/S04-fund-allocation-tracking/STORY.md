---
story: S04
epic: EPIC-13
title: Fund Allocation Tracking
status: ready
created: 2026-03-26T00:00:00.000000
effort: 6
---

# S04: Fund Allocation Tracking

## User Story

As a **shelter director**, I want to **categorize all spending by category (medical, food, operations, admin, fundraising) and show donors where their money goes** so that **donors see transparency and trust the organization, and EU funders receive the compliance reporting they require**.

## Acceptance Criteria

**Given** I record a financial transaction (expense or allocation)
**When** I categorize it
**Then** the transaction is tagged with one of: medical, food, operations, admin, fundraising, other

**Given** a donor views the fund allocation breakdown
**When** they open the transparency page
**Then** they see a pie chart showing percentage of funds allocated to each category

**Given** a donation is made to a specific campaign or cause
**When** the donation is recorded
**Then** the system tracks which fund category it belongs to and can report how that category's money was spent

**Given** EU funders require spending breakdowns
**When** I generate a compliance report
**Then** the report includes detailed fund allocation by category with supporting transaction details

**Given** I need to budget for next year
**When** I review historical fund allocation
**Then** I can see spending trends by category (medical increased 15%, food decreased 5%, etc.)

## Tasks

- T01: Extend transaction schema to include fund_category field with enum values
- T02: Build fund allocation dashboard showing breakdown and trends
- T03: Implement transaction categorization rules (auto-categorize based on expense type/vendor)
- T04: Create transparency page UI for public-facing fund allocation visualization
- T05: Add fund allocation breakdown to compliance and impact reports

## Definition of Done

- [ ] All transactions can be categorized by fund type
- [ ] Dashboard shows fund allocation breakdown as pie chart
- [ ] Transactions can be filtered and aggregated by fund category
- [ ] Public transparency page shows allocation breakdown (no sensitive vendor info)
- [ ] Compliance reports include detailed fund allocation with transaction-level support
- [ ] Unit tests cover categorization logic and aggregation (85%+ coverage)
- [ ] Integration tests verify fund allocation calculations across sample transactions
- [ ] Fund category totals match transaction sum exactly (no rounding errors)

## Technical Notes

- Fund category enum: medical, food, operations, admin, fundraising, other
- Transaction schema extension: fund_category (enum), allocation_reason (text)
- Auto-categorization: map expense_type or vendor_id to category using configuration table
- Pie chart data: SUM(amount) GROUP BY fund_category WHERE date BETWEEN start_date AND end_date
- Trend calculation: compare same period across multiple years
- Compliance breakdown format: category | total_amount | percentage | transaction_count | detail_transactions
- Public view: show only top-level breakdown, no vendor/recipient details

## Dependencies

- Depends on: EPIC-3 (Donation and transaction recording)
- Depends on: S03-impact-report-generator (fund allocation feeds into impact reports)
- Blocks: S05-outcome-metrics-analytics (outcome metrics require fund allocation context)

## Story Points: 6
