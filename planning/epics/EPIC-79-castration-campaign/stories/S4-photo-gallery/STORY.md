---
story: S4
epic: EPIC-79
ticket: RAP-528
title: "Photo gallery for completed castrations"
status: ready
points: 5
priority: P1
track: Fullstack
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S4: Photo gallery for completed castrations

## Story
As a **clinic**, I want **to upload proof photos of castrations** so that **donors can see the impact of their donations**.

## Description
Create photo upload system for clinics to submit before/after photos of castrated animals. Photos appear in campaign gallery with consent management.

## Acceptance Criteria
- [ ] When redeeming voucher: clinic can upload 1-3 photos (before/after/recovery)
- [ ] Photo upload: file input accepts JPEG/PNG, max 5MB per photo, shows preview
- [ ] Animal info: show animal name, species, age (from VetVoucher)
- [ ] Recovery date: optional field "Expected recovery date", shows in gallery
- [ ] Public consent: checkbox "Share photos publicly on campaign page", required before upload
- [ ] Photo validation: validate EXIF data (optional), warn if no date
- [ ] Storage: upload to cloud storage, store references in CastrationPhoto table
- [ ] CastrationPhoto model: id, vet_voucher_id, photo_url, photo_type (before|after|recovery), public_consent, uploaded_at, animal_name, notes
- [ ] Gallery page: /campaigns/castration/{id}/gallery shows all photos with consent=true
- [ ] Gallery display: grid layout, lazy-loaded, lightbox view, shows animal name and date
- [ ] Clinic dashboard: /clinic/redemptions shows uploaded photos with status and consent level
- [ ] Admin dashboard: /admin/castration-photos shows all photos with consent status, can mark as featured or remove if inappropriate

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test file upload, consent validation
- [ ] Component test: photo upload form renders
- [ ] Component test: file validation works
- [ ] Component test: gallery displays photos correctly
- [ ] Integration test: upload photo and see in gallery (if consent=true)
- [ ] Integration test: photos not shown if consent=false
- [ ] Manual testing: upload and verify in gallery
- [ ] Deployed to staging and verified

## Technical Notes
- Frontend: React file upload component in clinic redemption flow
- Backend: POST /api/vet-vouchers/{id}/photos endpoint
- File handling: validate MIME type, size, store in S3
- Cloud storage: use signed URLs for secure access
- Gallery: GET /api/campaigns/castration/{id}/gallery returns photos with consent=true
- Admin interface: /admin/castration-photos with filtering and moderation

## Story Points: 5
