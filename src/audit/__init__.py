"""Audit trail system for Refugio Animal Paraguay.

Provides middleware for automatic request auditing and utilities
for recording and querying audit log entries.
"""

from .middleware import AuditMiddleware
from .service import query_audit_logs

__all__ = [
    "AuditMiddleware",
    "query_audit_logs",
]
