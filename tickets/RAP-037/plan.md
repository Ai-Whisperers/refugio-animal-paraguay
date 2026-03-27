# RAP-037 Plan

## Objective
Build the staff-facing donation management dashboard as FastAPI endpoints: summary stats, enhanced filterable list, and CSV export.

## Description
The shelter needs a staff-facing donation dashboard so administrators can quickly view financial performance, filter donation history by date range / currency / payment method / fund category, and export records as CSV for accounting and reporting.

The current `GET /donations` endpoint is minimal (currency + status filters only). This ticket adds:
- `GET /donations/stats` — aggregated summary statistics by currency, period, and status
- `GET /donations/export` — streaming CSV download (staff only)
- Enhanced filters on `GET /donations` (date range, donor_id, fund_category, payment_method)

## Acceptance Criteria
- [ ] `GET /donations/stats` returns total donations, total amount by currency, by status breakdown, and by payment method breakdown (staff only, JWT required)
- [ ] `GET /donations/stats` accepts `date_from` and `date_to` query params to filter the period
- [ ] `GET /donations` accepts additional filters: `date_from`, `date_to`, `donor_id`, `fund_category`, `payment_method`
- [ ] `GET /donations/export` returns a CSV file with all matching donations (same filter params as list), staff only
- [ ] All new endpoints return 401 if no auth token, 403 if non-staff role
- [ ] Unit tests cover stats computation logic
- [ ] Integration tests cover all 3 endpoints (stats, enhanced list, export)
- [ ] Coverage maintained at ≥80%

## Complexity Assessment
**Track**: Complex Implementation

### Assessment result: Complex — touches 3 files (api, schemas, tests), adds streaming CSV export, adds aggregation queries with SQLAlchemy 2.x

## Approach
1. Add `DonationStatsResponse` schema with per-currency breakdown
2. Extend `GET /donations` with date range + additional filter params
3. Add `GET /donations/stats` aggregation endpoint (groupby currency, status, payment method)
4. Add `GET /donations/export` streaming CSV endpoint using `StreamingResponse`
5. Add unit tests for stats logic
6. Add integration tests for new endpoints

## Dependencies
- Depends on: RAP-009 (Stripe Foundation — done), RAP-007 (JWT auth — done)
- Blocked by: None

## Risks
- CSV streaming in async FastAPI: must use `StreamingResponse` with `io.StringIO` or generator — tested pattern
