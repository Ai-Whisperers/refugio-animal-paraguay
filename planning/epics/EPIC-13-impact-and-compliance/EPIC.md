---
id: EPIC-13
title: Impact & Compliance
description: EU funder reporting, GDPR compliance, audit trail, and outcome tracking for accountability and transparency
status: planning
priority: high
estimated_effort: 65 story points
stories_count: 5
target_version: V2-V5 (incremental)
---

# EPIC-13: Impact & Compliance

## Overview

Build the accountability layer that makes Refugio trustworthy to EU funders, compliant with GDPR, and transparent in operations. This epic delivers audit trails, impact reports, fund allocation tracking, and outcome metrics. Without this, accepting EU donations creates compliance risk.

## Why This Epic Matters

- **EU funder requirement**: Dutch/EU foundations audit fund usage and expect quarterly impact reports
- **GDPR legal obligation**: Processing EU donor data requires consent tracking, data export, and deletion workflows
- **Donor retention**: Transparency drives repeat giving — donors who see impact give 2.5x more (industry data)
- **Operational intelligence**: Outcome metrics (return rates, cost-per-adoption) inform strategy
- **Trust building**: Public impact data differentiates from informal rescue operations

## Scope

### In Scope
- Comprehensive audit trail (who did what, when)
- GDPR data management (consent, export, deletion)
- Impact report generation (PDF, quarterly/annual)
- Fund allocation tracking (where money goes)
- Outcome metrics (post-adoption success, return rates)
- Funder-specific reporting views

### Out of Scope
- EU sanctions list screening (manual for now)
- External audit firm integration
- Tax filing automation (provide data, not filing)
- Blockchain-based donation tracking (future)

## Stories

- [ ] S01: Audit Trail System
- [ ] S02: GDPR Data Management
- [ ] S03: Impact Report Generator
- [ ] S04: Fund Allocation Tracking
- [ ] S05: Outcome Metrics & Follow-up Analytics

## Version Allocation

| Story | Version | Rationale |
|-------|---------|-----------|
| S01: Audit Trail | V2 | Must exist before accepting EU donations |
| S02: GDPR Data Management | V2 | Legal requirement for EU donor data processing |
| S03: Impact Report Generator | V3 | First quarterly report needed ~3 months after launch |
| S04: Fund Allocation Tracking | V3 | Required for funder transparency |
| S05: Outcome Metrics | V4-V5 | Needs adoption follow-up data to accumulate |

## Dependencies

- **Requires**: EPIC-10 (user identity for audit), EPIC-3 (donation data), EPIC-2 (adoption outcomes)
- **Consumed by**: EPIC-7 (dashboard displays impact metrics), EPIC-3 (donation receipts reference compliance)

## Technical Considerations

### Audit Trail Architecture

```python
# Middleware approach — capture every authenticated action
class AuditMiddleware:
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.method in ("POST", "PATCH", "PUT", "DELETE"):
            await log_audit_event(
                user_id=request.state.user.id,
                action=f"{request.method} {request.url.path}",
                ip_address=request.client.host,
                status_code=response.status_code,
                timestamp=datetime.utcnow()
            )
        return response
```

### New Database Models

```
AuditLog
  - id, user_id (FK, nullable for system events)
  - action (VARCHAR), resource_type, resource_id
  - ip_address, user_agent
  - request_body_hash (SHA256, not raw — PII safety)
  - status_code, timestamp

GDPRConsent
  - id, user_id (FK), consent_type (marketing/data_processing/analytics)
  - granted_at, revoked_at, method (web_form/api/import)
  - ip_address

GDPRDataRequest
  - id, user_id (FK), request_type (export/deletion)
  - requested_at, completed_at, status

FundAllocation
  - id, donation_id (FK, nullable), category (medical/food/operations/admin/fundraising)
  - amount, currency, allocated_at, allocated_by (FK)

ImpactReport
  - id, report_type (quarterly/annual/funder_specific)
  - period_start, period_end, funder_id (FK, nullable)
  - generated_at, generated_by (FK), file_path
```

### GDPR Compliance Checklist

- [ ] Right to access (Article 15): Export all personal data on request
- [ ] Right to erasure (Article 17): Delete personal data on request (soft-delete + anonymize)
- [ ] Right to data portability (Article 20): Machine-readable export (JSON/CSV)
- [ ] Consent tracking (Article 7): Record when, how, what consent was given
- [ ] Data retention policy: Auto-flag records exceeding retention period
- [ ] Processing records (Article 30): Audit log satisfies this requirement

## Risks

| Risk | Mitigation |
|------|------------|
| GDPR deletion conflicts with financial records | Anonymize donor data but preserve donation amounts for accounting |
| Audit log grows large | Partition by month, archive >1 year to cold storage |
| Impact reports show poor metrics | Early reporting sets baseline — improvement trend matters more |
| Fund allocation tracking is manual | Start with manual categorization, add rules-based auto-categorization in V5 |
