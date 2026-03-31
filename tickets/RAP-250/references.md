# RAP-250 References

## Key Files

| File | Role |
|------|------|
| `src/schemas/operational_metrics.py` | Pydantic v2 response models |
| `src/services/operational_metrics_service.py` | Async service with aggregate SQL queries |
| `src/api/operational_dashboard.py` | FastAPI router (`/api/admin/operational-dashboard`) |
| `src/app.py` | Router registration (after og_image, alphabetical order) |
| `tests/unit/test_operational_metrics_service.py` | 22 unit tests (AsyncMock) |
| `tests/integration/test_operational_dashboard.py` | 15 integration tests (AsyncClient) |

## Story
`planning/epics/EPIC-51-operational-dashboard/stories/S1-dashboard-api-with-aggregated-metrics/STORY.md`

## PR
GitHub PR #375 — merged to develop 2026-03-29
