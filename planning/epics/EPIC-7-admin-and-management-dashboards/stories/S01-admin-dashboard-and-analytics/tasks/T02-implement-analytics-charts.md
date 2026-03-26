---
task: T02
story: S01
epic: EPIC-7
title: Implement analytics charts
status: ready
priority: medium
created: 2026-03-25T17:13:26.733863
---

# T02: Implement analytics charts

## Description

Add three data-visualization charts to the admin dashboard below the KPI cards created by T01. Charts are populated by a dedicated FastAPI endpoint that executes three parallel PostgreSQL aggregation queries using `date_trunc` bucketing. No client-side data fetching — data arrives fully formed from the server and is passed to the chart rendering layer as serializable props.

Three charts:
1. **Adoption trends** — line chart of adoption request counts per week over the last 12 weeks
2. **Animal status breakdown** — donut chart of current animal population grouped by status
3. **Monthly donation volume** — bar chart of total EUR donated per month for the last 6 months (plus the current partial month)

## Tech Stack

- **Python 3.12 + FastAPI** — async endpoint at `GET /admin/dashboard/charts`; same JWT guard as T01
- **SQLAlchemy 2.x + PostgreSQL 16** — `date_trunc('week')` and `date_trunc('month')` aggregation queries run in parallel via `asyncio.gather`
- **Pydantic v2** — `ChartDataResponse` schema with three typed sub-models
- **Frontend (TBD)** — chart rendering using whatever visualization library is chosen; line chart, donut chart, and bar chart components

## Acceptance Criteria

- [ ] `GET /admin/dashboard/charts` endpoint exists and requires `staff` or `admin` JWT
- [ ] Adoption trends dataset always contains exactly 12 entries, one per week, with zero-filled weeks that had no activity
- [ ] Animal status breakdown dataset contains one entry per distinct status present in the `animals` table, using Spanish display labels
- [ ] Donation volume dataset covers the 6 most recent complete calendar months plus the current partial month (7 entries maximum)
- [ ] All chart data is fetched server-side in a single parallel database round-trip
- [ ] Charts render correctly at all breakpoints: single-column mobile, two-column tablet, three-column desktop
- [ ] Empty states render a Spanish-language message when a dataset has no data — no JavaScript errors on null or empty arrays
- [ ] Adoption trend weeks with zero requests are included in the dataset (not omitted)

## Implementation Notes

### Endpoint and File Structure

The chart data endpoint lives in `src/routers/admin/dashboard.py` alongside the stats endpoint from T01. The response schema lives in `src/schemas/admin/dashboard.py`. The three Pydantic sub-models are `WeeklyAdoptionPoint`, `AnimalStatusPoint`, and `MonthlyDonationPoint`, all nested inside the top-level `ChartDataResponse` model.

### Parallel Aggregation Queries

The endpoint handler dispatches three SQLAlchemy async queries via `asyncio.gather`:

**Query 1 — Adoption trends**: Groups all `adoption_requests` rows created in the last 12 weeks by calendar week using PostgreSQL's `date_trunc('week', created_at)`. Returns pairs of (week_start datetime, count). After the query returns, the handler builds a 12-entry list by iterating over the 12 expected weekly buckets — for each bucket, it looks up the count from the query result or inserts zero if that week had no requests. The buckets are labeled `Sem 1` through `Sem 12` (oldest to newest). The zero-fill step is critical: the frontend must always receive exactly 12 data points to render a proper time-series line.

**Query 2 — Animal status breakdown**: Groups all rows in the `animals` table by `status` using a GROUP BY and COUNT. Returns pairs of (status string, count integer). The handler maps each raw status value to a Spanish display label using a fixed mapping: `available` becomes `Disponible`, `reserved` becomes `Reservado`, `adopted` becomes `Adoptado`, `medical` becomes `En tratamiento`, and `quarantine` becomes `En cuarentena`. Any status value not in this mapping is passed through unchanged as a fallback. No zero-filling here — statuses with no animals are simply absent from the dataset.

**Query 3 — Monthly donation volume**: Groups all `donations` rows by calendar month using `date_trunc('month', created_at)` and sums `amount_eur` per bucket. The time window covers from the start of the month six months ago through the current date (inclusive). After the query returns, the handler builds a list of entries for each of the 6 prior complete months plus the current partial month, zero-filling any month with no donations. Month labels are formatted as `MMM YY` using the `es-PY` locale (for example, `ene 25`, `feb 25`).

### ChartDataResponse Schema

The top-level Pydantic v2 response model contains three fields:

`adoption_trends` is a list of `WeeklyAdoptionPoint` objects. Each `WeeklyAdoptionPoint` has a `week_label` string (for example, `Sem 1`) and a `count` integer. The list always contains exactly 12 entries.

`animal_status_breakdown` is a list of `AnimalStatusPoint` objects. Each `AnimalStatusPoint` has a `status` string (the raw database value), a `label` string (the Spanish display name), and a `count` integer. The list contains one entry per distinct status present in the database; it may be empty if no animals exist.

`monthly_donations` is a list of `MonthlyDonationPoint` objects. Each `MonthlyDonationPoint` has a `month_label` string and a `total_amount_eur` Decimal. The list contains up to 7 entries (6 complete months plus the current partial month).

### Chart Visual Specifications

**Adoption trends line chart**: Renders a smooth line over time with week labels on the X-axis and request count on the Y-axis. The Y-axis should only show whole numbers (no decimals). Grid lines are horizontal only. If the dataset contains only zero values, the frontend renders an empty state message in Spanish: `Sin solicitudes de adopción en las últimas 12 semanas`.

**Animal status donut chart**: Renders a ring/donut shape with a hole in the center. Each status segment uses a distinct color: Disponible uses success green, Reservado uses primary blue, Adoptado uses purple, En tratamiento uses amber/orange, and En cuarentena uses danger red. A legend below the chart maps colors to Spanish labels. If the dataset is empty, the frontend renders: `Sin animales registrados`.

**Monthly donation volume bar chart**: Renders vertical bars with month labels on the X-axis and EUR amount on the Y-axis. The Y-axis is formatted with currency notation (e.g., `€1.2M`). Bars have rounded top corners. If the dataset is empty, the frontend renders: `Sin donaciones en los últimos 6 meses`.

### Responsive Layout

The three chart cards sit in a responsive grid below the KPI cards. On mobile (below 640px) the charts stack vertically as single-column. On tablet (640px to 1279px) adoption trends and animal status sit side-by-side in a two-column layout, with donation volume spanning the full width below. On desktop (1280px and wider) all three charts sit in a three-column layout with equal widths.

Each chart card has a card title in Spanish as a subheading. Charts have a fixed height of 200px on all breakpoints so the grid rows stay consistent. The card padding, border, and background styling match the KPI cards from T01 for visual consistency.

### Empty State Handling

The frontend must handle empty datasets gracefully without throwing errors. Each chart component checks whether its data array is empty before attempting to render. If empty, the component renders a centered paragraph with the Spanish empty state message in muted text. The empty state container matches the 200px chart height so the card dimensions stay consistent even when no data is available.

### Database Index Dependencies

The adoption trends query benefits from the composite index on `adoption_requests(status, created_at)` created for T01, since the query filters by date range. The donation volume query benefits from the composite index on `donations(created_at, amount_eur)` also created for T01. No additional indexes are needed for chart queries beyond what T01 already requires.

## Tests

Unit tests live in `tests/unit/admin/test_chart_data.py`. They verify:

- The adoption trends dataset always contains exactly 12 entries even when the database has no adoption requests.
- All 12 entries have `count = 0` when no requests exist.
- A request created in the current week appears in the last (most recent) bucket with `count = 1`.
- Two requests in the same week are aggregated into a single bucket with `count = 2`.
- The animal status breakdown maps raw `available` to the label `Disponible`.
- The animal status breakdown maps raw `medical` to the label `En tratamiento`.
- An unknown status value is passed through unchanged (fallback behavior).
- The monthly donations dataset always contains the expected number of entries for the current date (up to 7).
- Two donations in the same calendar month are summed into a single `MonthlyDonationPoint`.
- A month with no donations is included in the list with `total_amount_eur = 0`.

Each test follows the AAA pattern and uses a real PostgreSQL 16 test instance with Alembic-managed schema. The test database is seeded and torn down per test to ensure isolation.

## Related Issues

- EPIC-7
- S01
- T01 creates the KPI grid and the placeholder section below it where charts are injected
- T03 adds the real-time activity feed below the charts section
