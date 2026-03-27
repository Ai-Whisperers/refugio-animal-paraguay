---
story: S2
epic: EPIC-77
ticket: RAP-508
title: "Clinic service catalog with pricing"
status: ready
points: 5
priority: P0
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S2: Clinic service catalog with pricing

## Story
As a **clinic admin**, I want **to define what services I offer and their prices** so that **donors can purchase vouchers for specific services**.

## Description
Create ClinicService model to define services offered by each clinic with pricing. Each service has a service type, price in local currency, and description.

## Acceptance Criteria
- [ ] ClinicService model/table with columns: id (UUID PK), clinic_id (FK to VetClinic), service_type (enum: castration_dog|castration_cat|consultation|vaccination|surgery_minor|surgery_major|dentistry|parasite_treatment|vaccination_package), price_cents (integer, minimum 0), currency (enum: EUR|USD|PYG, default EUR), description (string, 10-500 chars), active (boolean, default true), created_at, updated_at
- [ ] POST /admin/clinics/{clinic_id}/services endpoint: creates new service for clinic, validates service_type is valid enum, validates price > 0 (in cents), validates description length, requires clinic admin auth
- [ ] GET /admin/clinics/{clinic_id}/services endpoint: list all services for clinic, includes pricing and descriptions, filters by active status, paginated results
- [ ] GET /clinics/{clinic_id}/public-services endpoint: public endpoint showing active services only (no pricing details visible to unauthenticated users, only price shown)
- [ ] PUT /admin/clinics/{clinic_id}/services/{id} endpoint: update service details including price, description, active status, requires clinic admin auth
- [ ] DELETE /admin/clinics/{clinic_id}/services/{id} endpoint: soft-delete service (set active=false), prevents deletion if service has active vouchers
- [ ] Service type enum: castration_dog, castration_cat, consultation, vaccination, surgery_minor, surgery_major, dentistry, parasite_treatment, vaccination_package
- [ ] Price stored in cents (e.g., EUR 25.50 stored as 2550)
- [ ] Response format includes readable price: {price_cents: 2550, currency: 'EUR', price_display: 'EUR 25.50'}
- [ ] Currency can vary per clinic (some may price in PYG, others in EUR)
- [ ] Bulk service creation: POST /admin/clinics/{clinic_id}/services/bulk endpoint accepts array of services, creates multiple services atomically
- [ ] Each clinic must have at least one active service to be useful
- [ ] Validation: price must be >= 100 cents (EUR 1.00 minimum), price must be <= 100000 cents (EUR 1000 max)

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test service creation, price validation, currency handling, soft delete
- [ ] Integration test: create service for clinic and retrieve it
- [ ] Integration test: bulk create services
- [ ] Integration test: update service price
- [ ] Integration test: public endpoint doesn't include admin-only fields
- [ ] Integration test: soft delete prevents deletion if vouchers exist
- [ ] Database migration created
- [ ] Deployed to staging and verified

## Technical Notes
- Backend: FastAPI endpoints in admin/clinics module
- Database: ClinicService table with FK to VetClinic, indexes on clinic_id, service_type, active
- Price handling: always store in cents (integer), convert display via format_price(price_cents, currency)
- Service types: hard-coded enum, could be extensible in future
- Soft delete: set active=false, never delete
- Bulk creation: use transaction to ensure atomicity
- Response schema: include price_display field for UI convenience
- Permissions: only clinic admins can manage their clinic's services

## Story Points: 5
