# RAP-254 Progress Log

---
## [2026-03-29 00:00] Ticket started
**Action**: Created ticket directory, plan, context, and feature branch `feature/RAP-254-exportable-dashboard-data`
**Findings**: donations.py has the CSV StreamingResponse pattern. Will follow same approach.
**Decision**: Two endpoints: /export/metrics (full snapshot) and /export/population (breakdown)
**Next**: Implement endpoints + tests

---
## [2026-03-29 14:33] RAP-254 complete
**Action**: Implemented CSV export endpoints, wrote 14 unit tests, ran ruff check, committed, pushed branch, created PR #379
**Findings**: `Depends(require_staff)` captures function reference at import time — patch() has no effect. Must use `app.dependency_overrides`. Also needed `@pytest_asyncio.fixture` (not `@pytest.fixture`) for async generator fixtures in STRICT asyncio mode.
**Decision**: Rewrote test file to use dependency_overrides pattern consistent with test_emergency_updates.py and test_homepage_content.py
**Next**: Awaiting PR review and merge
