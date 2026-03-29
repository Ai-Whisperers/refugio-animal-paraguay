# RAP-255 Plan

## Objective
Add a staff-accessible API endpoint that returns donation summaries aggregated by period (monthly/quarterly/annual), currency (EUR/PYG/USD), and donation type (payment method or target type).

## Acceptance Criteria
- [ ] GET /api/admin/financial-reporting/donation-summary returns aggregated totals
- [ ] Supports grouping by period (daily/weekly/monthly/quarterly/annual)
- [ ] Supports breakdown by currency (EUR/PYG/USD)
- [ ] Supports breakdown by type (payment_method or target_type)
- [ ] Only counts completed donations
- [ ] Auth: staff or admin required
- [ ] Unit tests passing (80%+ coverage)
- [ ] Ruff/black clean

## Complexity Assessment
**Track**: Simple Fix — single service + router, ≤5 files, well-understood query pattern.

## Approach
1. Create `src/services/donation_summary_service.py` with async aggregation queries
2. Create `src/api/financial_reporting.py` router with GET /donation-summary endpoint
3. Register router in `src/main.py`
4. Write unit tests in `tests/unit/test_donation_summary_service.py`

## Dependencies
- Depends on: `src/db/models/donation.py` (Donation model), existing auth deps
