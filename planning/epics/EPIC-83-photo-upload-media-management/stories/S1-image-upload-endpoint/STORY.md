---
story: S1
epic: EPIC-83
ticket: RAP-559
title: "Image upload endpoint with validation"
status: ready
points: 5
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S1: Image upload endpoint with validation

## Story
As a **staff member**, I want **to upload images to the system** so that **I can add photos to animals, campaigns, and content**.

## Description
Create the foundational image upload endpoint with file validation, storage, and metadata tracking. Endpoint accepts multipart form data, validates file type and size, generates unique filename, and returns metadata.

## Acceptance Criteria
- [ ] POST /api/media/upload multipart endpoint created (auth: user role required)
- [ ] Endpoint accepts single file in "file" form field
- [ ] File type validation: only accept jpg, jpeg, png, webp (MIME type checking, not just extension)
- [ ] File size validation: max 10MB (10485760 bytes), return 413 Payload Too Large if exceeded
- [ ] Magic bytes validation: verify file signature to prevent spoofed extensions
- [ ] Generate UUID filename: store as {uuid}.{original_extension}
- [ ] Response returns JSON: {id (UUID), url (path to serve), thumbnail_url (path to thumbnail), width (pixels), height (pixels), size_bytes}
- [ ] Media model created with fields: id (UUID), original_filename (string), storage_path (string), content_type (enum), size_bytes (int), width (pixels), height (pixels), uploaded_by (FK to User), created_at (datetime)
- [ ] Store metadata in Media table (see above schema)
- [ ] Filename collision detection: use UUID to guarantee uniqueness
- [ ] Error responses return structured error: {error, message, details if validation failed}
- [ ] HTTP 400 for validation errors (invalid type, too large)
- [ ] HTTP 403 for unauthorized access
- [ ] HTTP 500 for storage failures with appropriate message
- [ ] Files stored in /media/uploads/{year}/{month}/{day}/ directory structure (for organization)
- [ ] Database transaction: if storage fails, don't create Media record
- [ ] Unit tests cover: valid upload, file too large, invalid type, magic bytes mismatch
- [ ] Integration test for full upload flow

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for upload endpoint
- [ ] Error handling tested (all error cases)
- [ ] Deployed to staging and verified
- [ ] API documented in OpenAPI/Swagger

## Technical Notes
- Use python-magic-bin or similar for magic bytes validation
- Implement using FastAPI or Flask file upload handling
- Store uploaded file immediately to disk/S3
- Extract image dimensions using PIL.Image
- Add request size limit to prevent DOS attacks
- Log all upload attempts for audit trail
- Consider virus scanning (integrate ClamAV placeholder for future)

## Story Points: 5
