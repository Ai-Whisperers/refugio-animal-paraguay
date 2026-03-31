# RAP-536 Progress Log

---
## [2026-03-28 10:32] Ticket started
**Action**: Created ticket plan, context. Checked codebase state.
**Findings**: Campaign model exists, no rescuer_id field. Portal pattern follows rescuer_animals.py.
**Decision**: Add rescuer_id nullable FK to campaigns; create dedicated portal router.
**Next**: Migration → backend API → frontend → tests
