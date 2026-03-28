---
story: S1
epic: EPIC-77
ticket: RAP-507
title: "Partner veterinary clinic registration model and API"
status: done
points: 5
priority: P0
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S1: Partner veterinary clinic registration model and API

## Story
As a **platform admin**, I want **to register partner veterinary clinics** so that **they can redeem vouchers and provide services**.

## Description
Create the VetClinic model and API endpoints for admin to register and manage partner clinics. Store clinic contact information, banking details for reimbursement, and active status.

## Acceptance Criteria
- [ ] VetClinic model/database table with columns: id (UUID PK), name (string, 2-100 chars), address (string), city (string), phone (string, formatted), email (string), contact_person_name (string), contact_person_phone (string), services_offered (JSON array of service types), bank_account_holder (string), bank_account_number (string encrypted), bank_routing_code (string encrypted), bank_currency (enum: EUR|USD|PYG), active (boolean, default true), created_at, updated_at
- [ ] POST /admin/clinics endpoint: accepts JSON with all required fields, validates email format, validates phone format (+595), validates bank account format, validates contact person info, creates clinic with active=true
- [ ] GET /admin/clinics endpoint: list all clinics, supports filtering by active status and city, returns paginated results (limit 20, offset supported), includes clinic name and contact person
- [ ] GET /admin/clinics/{id} endpoint: retrieve single clinic with all details including services and bank info, requires admin auth
- [ ] PUT /admin/clinics/{id} endpoint: update clinic details, validates all fields, prevents changes to bank info without additional verification (stores change_requested flag), returns updated clinic
- [ ] DELETE /admin/clinics/{id} endpoint: soft-delete clinic (set active=false), prevents deletion if clinic has unredeemed vouchers
- [ ] Response format: {id, name, address, city, phone, email, contact_person_name, contact_person_phone, services_offered, bank_account_holder, active, created_at}
- [ ] Bank details are encrypted at rest and never returned in API responses (except masked version: last 4 digits visible)
- [ ] Admin-only access: all endpoints require admin role and proper authentication
- [ ] Validation: clinic name must be unique, email must be unique, phone must be valid format, address must be 5-200 characters

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test clinic creation, validation, updates, soft delete
- [ ] Integration test: create clinic and retrieve it
- [ ] Integration test: update clinic details
- [ ] Integration test: soft delete clinic
- [ ] Integration test: list clinics with pagination
- [ ] Security test: bank details encrypted and not exposed
- [ ] Security test: non-admin users cannot access clinic endpoints
- [ ] Database migration created and tested
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints in admin module, require admin role via auth middleware
- Database: VetClinic table with proper constraints and indexes on active, city, email
- Encryption: Use Fernet (symmetric encryption) for bank details, store key in environment variable
- Validation: email via regex RFC 5322, phone via +595 format, bank account format per country (Paraguay uses 8-digit account numbers)
- Response schema: exclude bank_account_number and bank_routing_code from normal responses, include only for updates with special flag
- Soft delete: set active=false, never actually delete records for audit trail
- Pagination: default limit 20, support offset parameter

## Story Points: 5
