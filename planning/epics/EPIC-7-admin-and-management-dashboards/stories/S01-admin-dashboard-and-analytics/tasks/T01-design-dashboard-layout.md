---
task: T01
story: S01
epic: EPIC-7
title: Design dashboard layout
status: ready
priority: medium
created: 2026-03-25T17:13:26.733805
---

# T01: Design dashboard layout

## Description

Build the admin dashboard shell: route protection, persistent sidebar navigation, and KPI metric cards showing shelter-wide statistics. This is the structural foundation that T02 (charts) and T03 (real-time metrics) extend. Access is restricted to authenticated users with `admin` or `staff` role, enforced server-side via a FastAPI JWT dependency guard before any data is fetched.

## Tech Stack

- **Python 3.12 + FastAPI** — async endpoint for `/admin/dashboard/stats`; JWT dependency guard for role enforcement
- **SQLAlchemy 2.x ORM + PostgreSQL 16** — four parallel async queries via `asyncio.gather`
- **Pydantic v2** — `DashboardStatsResponse` schema for typed response and automatic API documentation
- **Frontend (TBD)** — responsive KPI grid layout; sidebar navigation; skeleton loading states

## Acceptance Criteria

- [ ] `GET /admin/dashboard/stats` route exists and returns 401 for missing/invalid JWT
- [ ] Users without `admin` or `staff` role receive 403 on any `/admin/*` route
- [ ] Dashboard layout renders a persistent sidebar on desktop with all admin section links
- [ ] Sidebar collapses to a top-nav on mobile (below 1024px viewport width)
- [ ] Four KPI cards display: total animals, pending adoptions, active volunteers, monthly donations (₲)
- [ ] Each KPI card shows a trend direction vs. previous 30-day period (up/down/flat indicator)
- [ ] All KPI data is fetched in a single parallel database round-trip — no sequential queries
- [ ] Active sidebar link is visually highlighted based on current route

## Implementation Notes

### Route Structure

The backend exposes one endpoint at `GET /admin/dashboard/stats`. The frontend (TBD) renders the full dashboard shell around the data this endpoint returns. The backend router file lives in `src/routers/admin/dashboard.py`. The `DashboardStatsResponse` schema lives in `src/schemas/admin/dashboard.py`.

When the frontend framework is chosen, the admin shell will be organized as a layout wrapping all `/admin/*` pages. The sidebar component will be always visible on screens 1024px and wider and collapse to a hamburger/top-nav on narrower viewports. Sidebar links cover: Panel (exact match), Animales, Adopciones, Donaciones, Voluntarios, Usuarios, Configuración, and Reportes.

### JWT Auth Guard

The endpoint uses a FastAPI dependency named `require_staff_or_admin_role`. This dependency extracts the Bearer token from the `Authorization` header, decodes the JWT, fetches the user's profile from the `users` table, and verifies the `role` field is either `staff` or `admin`. If the token is missing or expired the dependency raises HTTP 401. If the role is not in the allowed set the dependency raises HTTP 403. No database fetch occurs in the endpoint handler itself until this dependency resolves successfully.

### Parallel Statistics Queries

The endpoint handler calls `asyncio.gather` with four separate SQLAlchemy async queries running concurrently:

1. **Total animals**: a COUNT on the `animals` table with no filters — returns total shelter population.
2. **Pending adoptions**: a COUNT on `adoption_requests` filtered by `status = 'pending'` — returns the current review backlog. Uses the composite index on `(status, created_at)`.
3. **Active volunteers**: a COUNT on `volunteer_assignments` filtered by `status = 'active'`.
4. **Donations comparison**: two sub-queries on the `donations` table. The first sums `amount_eur` for rows where `created_at` falls within the current 30-day window (now minus 30 days to now). The second sums `amount_eur` for rows where `created_at` falls within the prior 30-day window (now minus 60 days to now minus 30 days). Both use the composite index on `(created_at, amount_eur)`.

All four queries are dispatched simultaneously. The handler awaits all results before assembling the response. This ensures a single database round-trip regardless of the number of metrics.

### Trend Direction Logic

After the four queries complete, the endpoint computes a `trend` direction for each KPI that supports comparison. Trend direction is one of three string values: `"up"`, `"down"`, or `"flat"`.

For donations: if the prior 30-day sum is zero and the current sum is greater than zero, the trend is `"up"`. If both sums are zero, the trend is `"flat"`. Otherwise, calculate the percentage change as `(current - prior) / prior * 100`. If the absolute percentage change is below 5%, report `"flat"`. If the current period is higher, report `"up"`. If lower, report `"down"`.

The 5% flat zone prevents misleading trend arrows when the change is statistically insignificant noise.

### DashboardStatsResponse Schema

The Pydantic v2 response model contains the following fields: `total_animals` (integer), `pending_adoptions` (integer), `active_volunteers` (integer), `monthly_donations_eur` (Decimal, current 30-day sum in EUR), `monthly_donations_pyg` (Decimal, current 30-day sum in PYG local currency), `donations_trend` (string — up/down/flat), `animals_trend` (string — up/down/flat, comparing current 30-day new arrivals to prior 30-day new arrivals), `generated_at` (ISO 8601 datetime when the response was assembled). All monetary fields use Decimal rather than float to avoid floating-point rounding errors.

### KPI Card Design

The frontend renders four KPI cards in a responsive grid. The grid is single-column on mobile, two-column on screens 640px and wider, and four-column on screens 1280px and wider. Each card shows: a label in Spanish (Animales registrados, Adopciones pendientes, Voluntarios activos, Donaciones 30d), the numeric value in large bold text, and a trend indicator below using green for `"up"`, red for `"down"`, and neutral gray for `"flat"`.

Monetary values are formatted as `₲ 1.234.567` using the `es-PY` locale. The trend indicator shows an upward or downward arrow alongside the period-over-period delta amount.

### Skeleton Loading and Error Handling

While the stats request is in flight the frontend renders skeleton placeholder cards matching the exact dimensions of the real KPI cards. This prevents layout shift on load.

If the stats request fails, the frontend retries automatically up to three times with exponential back-off starting at 500ms. After three failures it shows an error banner above the KPI area with a manual retry button. The sidebar and page chrome remain fully functional during a stats failure — only the KPI data area enters the error state.

### Database Indexes Required

The queries in this task depend on two composite indexes that must exist before deployment:

- `adoption_requests(status, created_at)` — supports the pending adoption count filtered by status with optional date range.
- `donations(created_at, amount_eur)` — supports the date-range sum queries used for trend calculation. This is an index-only scan candidate when both columns are covered.

Both indexes should be created via Alembic migration as part of Phase 1 schema setup, not added ad-hoc. The migration file should live in `alembic/versions/` alongside the table creation migrations.

## Tests

Unit tests live in `tests/unit/admin/test_dashboard_stats.py`. They verify:

- When all tables are empty the endpoint returns zeros and all trends are `"flat"`.
- When current donations exceed prior by more than 5%, `donations_trend` is `"up"`.
- When current donations are less than prior by more than 5%, `donations_trend` is `"down"`.
- When the change is within 5% of prior, `donations_trend` is `"flat"`.
- When prior is zero and current is greater than zero, `donations_trend` is `"up"` (not a division-by-zero error).
- When both prior and current are zero, `donations_trend` is `"flat"`.
- A request with a missing JWT returns 401.
- A request with a valid JWT for an `adopter` role returns 403.

Each test follows the AAA pattern. The database session is injected via a pytest fixture that uses a test PostgreSQL instance. No Supabase or mock database — tests run against a real PostgreSQL 16 instance seeded via Alembic.

## Related Issues

- EPIC-7
- S01
- T02 adds analytics charts below the KPI grid
- T03 adds real-time activity feed below the charts
