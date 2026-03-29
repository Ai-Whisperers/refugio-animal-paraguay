# RAP-273 Progress Log

---
## [2026-03-29] Implemented
**Action**: Created suspicious activity detection service and API
**Findings**: No existing detection beyond account lockout. Built from scratch using audit log aggregate queries.
**Decision**: Heuristic thresholds with clear constants — easy to tune
**Next**: Tests pass, committing
