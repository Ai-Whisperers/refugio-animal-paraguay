---
story: S1
epic: EPIC-89
ticket: RAP-604
title: "Expense recording system"
status: ready
points: 6
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S01: Expense Recording System

## Story

As a staff member, I want to record all expenses in a central system so that the organization can track spending and demonstrate financial accountability to donors.

## Description

Implement database schema and API endpoints for expense recording. Create Expense model with categories, amounts, dates, receipt storage, and approval workflow. Track which expenses are approved and by whom for audit purposes.

## Acceptance Criteria

- [ ] Create Expense model in database with fields:
  - [ ] amount_cents (integer, amount in cents)
  - [ ] currency (enum: PYG, USD, EUR)
  - [ ] category (enum: medical, food, shelter, rescue, operations, transport, admin)
  - [ ] description (text)
  - [ ] receipt_url (text, nullable, path to uploaded receipt image)
  - [ ] expense_date (date, when the expense occurred)
  - [ ] recorded_by (FK to User, who recorded it)
  - [ ] approved_by (FK to User, nullable, admin who approved)
  - [ ] status (enum: pending, approved, rejected)
  - [ ] created_at (timestamp)
  - [ ] updated_at (timestamp)
- [ ] Create database migration to add expenses table
- [ ] Implement GET /admin/expenses - list all expenses with filters
- [ ] Implement POST /admin/expenses - create new expense (requires admin role)
- [ ] Implement GET /admin/expenses/{id} - get expense details
- [ ] Implement PUT /admin/expenses/{id} - edit expense (if not approved)
- [ ] Implement DELETE /admin/expenses/{id} - delete expense (if not approved)
- [ ] Implement PATCH /admin/expenses/{id}/approve - approve expense
- [ ] Implement PATCH /admin/expenses/{id}/reject - reject with reason
- [ ] Validate that amount is positive integer
- [ ] Validate that date is not in future
- [ ] Validate category is valid enum value
- [ ] Return 400 Bad Request for invalid input
- [ ] Return 403 Forbidden for non-admin users
- [ ] Return 404 Not Found for nonexistent expense
- [ ] Include created_by user info in response (name, email)
- [ ] Include approved_by user info if approved
- [ ] Support filtering by: category, status, date_from, date_to, created_by

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Database schema reviewed and tested
- [ ] Migration runs cleanly on test database
- [ ] API endpoints tested with Postman or similar
- [ ] Unit tests for validation logic
- [ ] Integration tests for all CRUD operations
- [ ] Access control tested (admin only)
- [ ] Error handling tested for edge cases
- [ ] Response format documentation
- [ ] Database constraints verified (foreign keys, types)
- [ ] Performance verified for queries
- [ ] Deployed to staging and verified

## Technical Notes

- Use SQLAlchemy for ORM
- Store amounts in cents to avoid floating point issues
- Use enum types from Python enum module
- Implement soft delete for audit trail (mark as deleted, don't remove)
- Index on recorded_by, category, expense_date for fast queries
- Validate receipt_url is valid S3 or storage path
- Use database transactions for atomic operations
- Consider archiving old expenses for performance

## Story Points: 5
