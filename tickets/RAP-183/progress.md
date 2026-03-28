# RAP-183 Progress Log

---
## [2026-03-28 20:00] Session start
**Action**: Started RAP-183 — Attendance tracking and no-show flags
**Findings**: ShiftSignup.attended field exists (bool | None). No attendance endpoints exist yet.
**Decision**: Add GET signups list + PATCH attended to shifts.py. Admin detail page.
**Next**: Implement backend endpoints
