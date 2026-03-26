# RAP-039 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26 18:10

## Current Focus
Building GDPR data export backend — model, service, API endpoints.

## Technical State
- **Branch**: feature/RAP-039-gdpr-data-export
- **Base**: develop

## Next Steps
1. Create DataExportRequest model
2. Create Alembic migration
3. Build GDPR export service
4. Create schemas and API endpoints
5. Write tests

## Blockers
None.

## Key Decisions Made
- Synchronous export generation (no background job yet — infrastructure not ready)
- Export data stored as JSONB in the data_export_requests row (no file system dependency)
- Download tracked via downloaded_at timestamp
- Export expires after 7 days (soft enforcement — data not deleted, just marked expired)
