# RAP-039 Plan

## Objective
Implement GDPR Article 15/20 data export functionality allowing donors, adopters, and staff to request and download their personal data in JSON format.

## Description
EU donors and adopters have the right to access and port their personal data under GDPR. This ticket implements the backend infrastructure for data export requests: a tracking model, aggregation service that collects personal data across all tables, and REST API endpoints for requesting and downloading exports.

## Acceptance Criteria
- [ ] DataExportRequest model tracks export requests with status lifecycle
- [ ] POST /gdpr/data-export creates an export request and generates the export
- [ ] GET /gdpr/data-export/{id}/download returns the JSON export data
- [ ] GET /gdpr/data-export lists a user's export requests
- [ ] Export JSON includes: profile, donations, adoption records, consents, audit trail
- [ ] Donor exports include donation history and in-kind donations
- [ ] Adopter exports include adoption requests
- [ ] Staff exports include audit log entries where they are the actor
- [ ] Export requests are audit-logged
- [ ] Download links track access (downloaded_at timestamp)
- [ ] Unit tests for data aggregation logic (90%+ coverage)
- [ ] Integration tests for API endpoints

## Complexity Assessment
**Track**: Complex Implementation

**Assessment result**: Complex — multiple data sources to aggregate, cross-model queries, role-based export content, security considerations.

## Approach
1. Create DataExportRequest model with status (pending, processing, completed, expired, failed)
2. Alembic migration for data_export_requests table
3. Build GDPRExportService that aggregates personal data by subject type (donor, adopter, staff)
4. Create schemas for request/response
5. Build API endpoints under /gdpr prefix
6. Comprehensive tests

## Dependencies
- Depends on: existing user, donor, adopter, donation, adoption_request, consent, audit_log models
- No blocking dependencies

## Risks
- Risk: Large data volumes for active donors → Mitigation: Synchronous for now, background job in future
- Risk: PII in audit_log old_values/new_values JSONB → Mitigation: Include but document in export schema
