"""Audit trail system for GDPR Article 30 compliance.

Provides automatic logging of authenticated actions and admin query API.
"""

from src.audit.service import AuditService, record_audit

__all__ = [
    "AuditService",
    "record_audit",
]
