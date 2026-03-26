---
story: S02
epic: EPIC-4
title: Veterinary Notes & Documents
status: ready
created: 2026-03-25T17:13:26.730326
version: V4
---

# S02: Veterinary Notes & Documents

## Description

System for uploading, storing, and managing veterinary documents (notes, exam reports, x-rays, test results) with full-text search capability.

## Acceptance Criteria

**Given** a vet visits to examine an animal
**When** they access the animal's medical record
**Then** they see a "Add Examination" button to create new vet notes with date, vet name, findings, and diagnosis fields

**Given** a vet completes an exam
**When** they save notes
**Then** notes are stored with timestamp, vet_id, animal_id, and searchable text content added to full-text index

**Given** exam report or test results exist as files
**When** vet uploads document
**Then** file is stored (PDF, image, etc.), virus-scanned, stored securely, indexed by filename/type, and linked to medical record

**Given** multiple documents are stored
**When** staff views animal's medical documents
**Then** documents are displayed in chronological order with file type icons, upload date, and download/view buttons

**Given** I search for a medical term
**When** I use the full-text search
**Then** results show matching medical notes and document filenames containing the term

**Given** a veterinary document is uploaded
**When** the file is processed
**Then** document metadata (upload date, vet name, filename) is stored alongside actual file for tracking provenance

**Given** sensitive medical information is stored
**When** documents are accessed
**Then** access is logged in audit trail, and only staff with medical access role can view

## Tasks

- T01: Build document upload system
- T02: Create notes interface
