---
story: S2
epic: EPIC-83
ticket: RAP-560
title: "Image optimization pipeline"
status: ready
points: 5
priority: P0
track: Backend
sprint: 12
version: V1
created: 2026-03-27T20:00:00
---

# S2: Image optimization pipeline

## Story
As a **system**, I want **to automatically optimize uploaded images** so that **pages load quickly and storage is used efficiently**.

## Description
Implement image optimization processing that runs on upload. Resizes images to web-friendly dimensions, generates thumbnails, and converts to WebP format for modern browsers while keeping original as fallback.

## Acceptance Criteria
- [ ] On upload, image is processed with three versions: original (fallback), optimized (max 1920px wide), thumbnail (400px width)
- [ ] Resize maintains aspect ratio: if image is 4000x2000, resizing to 1920 wide produces 1920x960
- [ ] If image smaller than 1920px wide, don't upscale (keep original size)
- [ ] Generate thumbnail at exactly 400px wide with aspect ratio maintained
- [ ] Convert optimized and thumbnail to WebP format (.webp extension)
- [ ] Store original in original format (.jpg, .png) as fallback
- [ ] File storage structure: /media/uploads/{year}/{month}/{day}/{uuid}/{original|optimized|thumbnail}.{format}
- [ ] Processing uses Pillow (PIL) for image manipulation
- [ ] Processing happens synchronously during upload (return doesn't need to wait for background processing, but initial response should succeed)
- [ ] Media model extended with fields: has_optimized (bool), has_thumbnail (bool), optimization_status (enum: pending, processing, complete, failed)
- [ ] If optimization fails, original uploaded file is still usable (graceful degradation)
- [ ] Optimization status tracked in Media record for debugging
- [ ] EXIF data stripped during optimization (privacy: no geolocation, camera info)
- [ ] Compressed to reasonable quality: WebP 85% quality, JPG 85% quality
- [ ] Unit tests cover: resize logic, aspect ratio preservation, thumbnail generation, format conversion
- [ ] Integration test for full optimization pipeline

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage)
- [ ] Integration test for optimization pipeline
- [ ] Image quality verified (visual comparison of original vs optimized)
- [ ] File size reduction measured and documented
- [ ] Performance tested: upload doesn't block response
- [ ] Deployed to staging and verified

## Technical Notes
- Use PIL/Pillow for image processing
- Consider using Celery or similar for async background processing if synchronous is too slow
- Implement quality settings as environment variables for tuning
- Log optimization metrics: original size, optimized size, compression ratio
- Add metrics for optimization time
- Consider WebP support detection for content negotiation

## Story Points: 5
