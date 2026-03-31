# RAP-254 Recap

## Outcome
Delivered as planned: two CSV export endpoints for the operational dashboard, following the existing `StreamingResponse` + `io.StringIO` + `csv.writer` pattern from `donations.py`.

## Acceptance Criteria — Final Status
- [x] `GET /export/metrics` returns `text/csv` with `Content-Disposition: attachment; filename=dashboard-metrics.csv`
- [x] Metrics CSV contains all key fields: generated_at, occupancy rate, avg LOS, species counts, population breakdown
- [x] `GET /export/population` returns 7-row breakdown (one per status) with `occupancy_contribution` boolean column
- [x] Both endpoints require staff auth via `require_staff`
- [x] 14 unit tests covering status codes, headers, row counts, and field values

## Key Learnings
- FastAPI `Depends(callable)` captures the callable reference at function definition time. Patching the module-level name afterward has no effect. Always use `app.dependency_overrides` to bypass auth/DB dependencies in unit tests.
- Async generator fixtures in STRICT asyncio mode require `@pytest_asyncio.fixture`, not `@pytest.fixture`.

## Validation Evidence
- Tests: 14 passing, 0 failing
- Ruff: clean on all changed files
- PR: #379 created targeting develop
