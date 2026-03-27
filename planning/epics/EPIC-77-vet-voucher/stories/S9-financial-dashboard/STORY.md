---
story: S9
epic: EPIC-77
ticket: RAP-515
title: "Financial reconciliation dashboard"
status: ready
points: 5
priority: P2
track: Fullstack
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S9: Financial reconciliation dashboard

## Story
As an **admin**, I want **to view financial reconciliation data for voucher program** so that **I can track payments, clinics' outstanding balances, and prepare settlements**.

## Description
Create admin dashboard for financial tracking of voucher program. Shows total vouchers sold vs redeemed, outstanding balances per clinic, payment status, and settlement reports.

## Acceptance Criteria
- [ ] /admin/voucher-finance page accessible to admin users only
- [ ] Summary section at top: total vouchers purchased (count), total vouchers redeemed (count), redemption rate (%), total vouchers expired (count)
- [ ] Summary section: total money collected (sum of all donations), total money owed to clinics (sum of redeemed vouchers by clinic)
- [ ] Clinic breakdown table: columns: clinic name, active vouchers (count), redeemed vouchers (count), amount redeemed (sum), outstanding balance (owed to clinic), last payment date, payment status (paid|pending|overdue)
- [ ] Click on clinic row: shows detail view with: all vouchers for that clinic, grouped by status (redeemed, claimed, purchased, expired), timeline of payments
- [ ] Outstanding balance calculation: sum of redeemed vouchers minus sum of payments made to clinic
- [ ] Payment tracking: Payment model storing: clinic_id, amount_cents, payment_method, paid_at, reference_id (bank transfer ref), notes
- [ ] Monthly settlement report: shows by month: total redeemed, total paid to clinics, variance
- [ ] Export functionality: "Download Settlement Report" button returns CSV file with: month, clinic_name, total_redeemed, amount_owed, amount_paid, outstanding_balance
- [ ] Filter by date range: date picker for start and end date, recalculates all numbers based on filter
- [ ] Currency handling: display all amounts in EUR (or configurable currency), show currency symbol
- [ ] Pagination: if many clinics, paginate table (limit 10 per page)
- [ ] Search: filter clinics by name
- [ ] Color coding: outstanding balance cells highlighted (red if > 30 days overdue, yellow if 15-30 days)
- [ ] GET /api/admin/vouchers/finance/summary endpoint: returns JSON with summary stats
- [ ] GET /api/admin/vouchers/finance/clinics endpoint: returns paginated clinic breakdown
- [ ] GET /api/admin/vouchers/finance/clinics/{clinic_id} endpoint: detailed view for clinic
- [ ] GET /api/admin/vouchers/finance/report?start_date=...&end_date=... endpoint: settlement report
- [ ] CSV export format: headers: Month, Clinic Name, Total Redeemed, Amount Owed, Amount Paid, Outstanding Balance

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test calculations, filtering, export format
- [ ] Integration test: dashboard shows correct totals
- [ ] Integration test: clinic breakdown shows correct outstanding balance
- [ ] Integration test: monthly settlement report calculated correctly
- [ ] Integration test: CSV export format is correct
- [ ] Integration test: date range filtering works
- [ ] Component test: responsive UI on desktop
- [ ] Manual testing: verify calculations with sample data
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React page at pages/admin/voucher-finance.tsx with table and summary cards
- Backend: FastAPI endpoints in admin module, complex queries with aggregation
- Database queries: use GROUP BY and SUM aggregations, consider materialized views for performance
- Payment tracking: Payment model with clinic_id, amount_cents, paid_at, reference_id
- Outstanding balance: sum(redeemed vouchers) - sum(payments) per clinic
- CSV generation: use Python csv module or pandas, return as download
- Export file naming: voucher_settlement_report_2026-03-27.csv
- Performance: cache summary stats (5-minute TTL) since calculations are expensive
- Clinic details: use separate endpoint for detail view to avoid loading all clinics
- Sorting: allow sorting by clinic name, outstanding balance, redemption count
- Color coding: use Tailwind CSS conditional classes for red/yellow highlighting

## Story Points: 5
