# RAP-273 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-29

## Technical State
- Service: src/services/suspicious_activity_service.py
- API: src/api/admin_suspicious_activity.py (registered in app.py)
- Tests: tests/unit/test_suspicious_activity_service.py (10 tests)
- Detects: bulk_delete (HIGH), bulk_export (MEDIUM), gdpr_erasure_burst (HIGH), high_frequency_activity (LOW)
