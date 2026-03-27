---
story: S3
epic: EPIC-88
ticket: RAP-598
title: "Camera integration for forms"
status: ready
points: 7
priority: P0
track: Fullstack
sprint: 14
version: V14
created: 2026-03-27T20:00:00
---
# S03: Camera Integration for Forms

## Story

As a rescuer or adopter, I want to take photos directly from my phone camera when filling out forms so that I can quickly document animals or home conditions without leaving the form.

## Description

Implement camera integration using HTML5 File API and device camera access across the adoption application, vet notes, and voucher redemption forms. Allow users to take photos directly from camera or select from gallery, with image preview and compression before upload.

## Acceptance Criteria

- [ ] Adoption application form: add "Take photo of your home" button that opens camera
- [ ] Camera button uses <input type="file" accept="image/*" capture="environment"> for rear camera
- [ ] Camera button labeled clearly: "Tomar foto de tu hogar" (Take photo of your home)
- [ ] Vet notes form: add "Tomar foto" button for documentation photos
- [ ] Vet notes: camera captures environment (not selfie camera)
- [ ] Voucher redemption form: add "Tomar foto del animal" button (Take photo of animal)
- [ ] After photo taken, display preview on form before user submits
- [ ] Preview image shows in small thumbnail (150x150px) next to form field
- [ ] User can retake photo by clicking preview or camera button again
- [ ] User can remove selected photo with delete/X button
- [ ] Implement image compression using client-side library (e.g., browser-image-compression)
- [ ] Compress photos to maximum 2MB file size before upload
- [ ] Preserve EXIF data where possible for metadata
- [ ] Show compression progress if image >5MB
- [ ] Handle camera permission denied gracefully: show message "Camera permission required"
- [ ] Fall back to file input (pick from gallery) if camera not available
- [ ] Test on iOS Safari, Android Chrome, Firefox mobile

## Definition of Done

- [ ] Code complete, peer reviewed
- [ ] Camera permission handling tested
- [ ] Image compression working on mobile browsers
- [ ] Preview display tested on 375px viewport
- [ ] Integration with form submission verified
- [ ] Unit tests for image compression, preview rendering
- [ ] E2E test for adoption form with camera upload
- [ ] Manual testing on actual iOS device (iPhone)
- [ ] Manual testing on actual Android device
- [ ] Fallback to file picker verified on unsupported browsers
- [ ] Deployed to staging and verified

## Technical Notes

- Use browser-image-compression or similar library for client-side compression
- Handle iOS camera permission request (user must grant permission)
- Test EXIF orientation handling (photos may be rotated on iOS)
- Use Blob/File API for client-side image manipulation
- Implement abort/cancel functionality for camera access
- Consider data:// URLs or Blob URLs for preview display
- Test on Safari iOS (different permissions model than Android)
- Verify photos are properly oriented after compression

## Story Points: 5
