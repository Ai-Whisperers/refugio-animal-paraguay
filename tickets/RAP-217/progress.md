# RAP-217 Progress Log

---
## [2026-03-29] Ticket started
**Action**: Started implementation of campaign scheduling
**Decision**: EmailCampaign links to EmailList (RAP-215) and EmailTemplate (RAP-216 — but template is in a separate branch, so we reference by UUID without FK for now to avoid conflicts)
**Next**: Create model and migration
