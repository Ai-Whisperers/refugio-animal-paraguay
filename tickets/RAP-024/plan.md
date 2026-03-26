# RAP-024 Plan

## Objective
Implement an audit trail system that automatically logs all authenticated actions with GDPR Article 30 compliance.

## Description
Create database model, middleware, and API endpoints for a complete audit trail. The middleware intercepts authenticated requests (POST/PUT/DELETE/PATCH) and records who did what, when, from where. Admin/compliance endpoints provide filtered querying and CSV/JSON export.

## Acceptance Criteria
- [ ] AuditLog SQLAlchemy model with proper indexes
- [ ] Alembic migration for audit_logs table
- [ ] AuditAction enum covering: create, update, delete, view, approve, reject, assign, export, generate_report
- [ ] Middleware captures all authenticated write requests automatically
- [ ] Records: user_id, action, resource_type, resource_id, timestamp, ip_address, user_agent, old_values, new_values
- [ ] GET /admin/audit-logs endpoint with filters (user_id, action, resource_type, date range)
- [ ] GET /admin/audit-logs/export endpoint (CSV and JSON)
- [ ] Endpoints restricted to admin role
- [ ] No sensitive data (passwords, tokens) in logs
- [ ] Unit + integration tests

## Complexity Assessment
**Track**: Complex Implementation
- Multiple files: model, migration, middleware, schemas, API endpoints, tests
- New DB table with migration
- Middleware integration with existing auth system

## Approach
1. Create AuditLog model and AuditAction enum
2. Create Alembic migration
3. Create audit schemas (response, query params)
4. Implement audit middleware
5. Create admin audit API endpoints (list with filters, export)
6. Write tests
7. Quality gates

## Dependencies
- Depends on: JWT auth (RAP-007, done), middleware infrastructure (RAP-022, done)

## Risks
- Risk: Middleware overhead on every request → Mitigation: async DB write, keep payload minimal
