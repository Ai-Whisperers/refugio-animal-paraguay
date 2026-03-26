---
story: S04
epic: EPIC-1
title: Photo Upload & Management
status: ready
created: 2026-03-25T17:13:26.726661
version: V1
---

# S04: Photo Upload & Management

## Description

Cloudinary integration for uploading, storing, and managing animal photos with automatic resizing and optimization.

## Acceptance Criteria

**Given** I have staff or admin permissions
**When** I view an animal's edit page
**Then** I see a photo upload area where I can drag-and-drop or select multiple image files

**Given** I upload an image file
**When** the file is processed
**Then** Cloudinary automatically resizes the image (thumbnail: 300x300, detail: 800x800, full: 2000x2000) and stores optimized versions

**Given** an animal has multiple photos
**When** I manage the photos
**Then** I can reorder them (drag-and-drop or up/down buttons), set a primary photo, and delete unwanted photos

**Given** I delete a photo from an animal's profile
**When** the deletion is confirmed
**Then** the image is removed from Cloudinary and the database record is updated

**Given** an image is displayed on the animal catalog page
**When** the page loads
**Then** the appropriate sized version (300x300 thumbnail) is served with lazy loading and proper alt text

**Given** I view an animal detail page with multiple photos
**When** the gallery loads
**Then** high-quality versions (800x800+) are loaded progressively as I navigate through photos

## Tasks

- T01: Integrate Cloudinary SDK
- T02: Build upload component
