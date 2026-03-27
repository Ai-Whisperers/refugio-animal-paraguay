---
story: S5
epic: EPIC-83
ticket: RAP-563
title: "Medical document upload with validation"
status: ready
points: 3
priority: P1
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S5: Medical document upload with validation

## Story
As a **vet staff member**, I want **to upload medical documents** so that **I can attach vaccination records, surgery reports, and health certificates to vet visits**.

## Description
Create specialized document upload endpoint for medical records. Supports PDF and image formats, includes file type validation via magic bytes, and integrates with vet visit records.

## Acceptance Criteria
- [ ] POST /api/vet-visits/{id}/documents/upload multipart endpoint created (auth: vet_staff role)
- [ ] File type validation: accept pdf, jpg, jpeg, png only (MIME type and magic bytes validation)
- [ ] File size limit: max 20MB (20971520 bytes), return 413 if exceeded
- [ ] Magic bytes validation: verify PDF signature (25504446...) and image signatures
- [ ] Generate UUID filename, store in /media/medical/{year}/{month}/{day}/{uuid}/{filename}
- [ ] VetDocument model created: id (UUID), vet_visit_id (FK), media_id (FK), document_type (enum: vaccination, surgery_report, health_cert, lab_result, xray, other), description (text), uploaded_by (FK to User), created_at
- [ ] Response returns JSON: {id, document_type, url, uploaded_date, uploaded_by_name}
- [ ] Document is linked to vet visit immediately
- [ ] Error responses: 400 for validation, 403 for unauthorized, 404 if vet visit not found, 500 for storage
- [ ] Virus scanning placeholder: log warning if ClamAV not available, but don't block upload (marked as unscanned)
- [ ] Unit tests: valid upload, invalid type, file too large, vet visit not found
- [ ] Integration test: upload medical document, verify linked to vet visit

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for upload endpoint
- [ ] Virus scanning integration tested (placeholder)
- [ ] Error handling tested (all error cases)
- [ ] Deployed to staging and verified

## Technical Notes
- Use same upload infrastructure as image uploads (POST /api/media/upload wrapper)
- Store document_type as enum for filtering
- Add description field for staff notes about document
- Consider PDF preview generation for documents
- Log all medical document access for audit trail
- Consider encryption for medical documents (future enhancement)

## Story Points: 3
