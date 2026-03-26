"""Audit trail system for Refugio Animal Paraguay.

Provides middleware for automatic request auditing and utilities
for recording and querying audit log entries.
"""

from .middleware import AuditMiddleware
from .service import create_audit_entry, query_audit_logs

__all__ = [
    "AuditMiddleware",
    "create_audit_entry",
    "query_audit_logs",
]
