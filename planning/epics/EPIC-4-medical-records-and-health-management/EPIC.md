---
epic: EPIC-4
title: Medical Records & Health Management
status: ready
created: 2026-03-25T17:13:26.729875
updated: 2026-03-25T17:13:26.729877
---

# EPIC-4: Medical Records & Health Management

## Overview

**Goal**: Build a comprehensive veterinary records system that tracks every animal's complete medical history from intake through adoption, enabling shelter staff and veterinarians to make informed care decisions and satisfy Paraguayan legal requirements for animal health documentation.

**Why it matters**: A shelter accepting animals from the street, from owner surrenders, and from other organizations has no prior medical history for most animals. Building a structured medical record from the moment of intake serves multiple purposes: it enables continuity of care when different staff members or volunteers handle the same animal; it provides adopters with documented evidence of vaccinations and treatments; it satisfies Paraguayan veterinary regulations that require shelter records to be maintained; and it creates data that the admin dashboard can use to track shelter-wide health costs and trends.

**Target users**: Shelter veterinarians who record diagnoses, treatment plans, and clinical notes; shelter staff who record routine observations, medication administrations, and vaccination events; shelter administrators who need aggregate health metrics; adopters who receive a copy of their adopted animal's medical summary.

---

## Scope

### In Scope

- PostgreSQL schema for medical records: one medical record per veterinary visit or event, with fields for date, attending veterinarian or staff member, record type (intake examination, routine checkup, illness treatment, surgery, vaccination, medication administration), clinical notes, and diagnosis codes
- Vaccination tracking: recording vaccine name, manufacturer lot number, date administered, and next due date; generating a vaccination schedule that alerts staff when vaccinations are overdue
- Medication tracking: recording active medications with dosage, frequency, start date, and end date; a view of currently active medications for any animal at a glance
- File attachment support: storing PDFs and images of external veterinary lab reports, X-rays, and health certificates associated with specific records
- Medical timeline: a chronological view of all medical events for a specific animal, accessible to authorized staff and veterinarians
- Medical hold status integration: the ability to place an animal on medical hold (updating its status in EPIC-1) and record the clinical reason, ensuring the animal is not listed as available for adoption while under active treatment
- A public-facing health summary: a brief, non-clinical summary of an animal's known vaccinations and sterilization status, suitable for display on the public animal profile without exposing detailed clinical notes

### Out of Scope

- Telemedicine or remote veterinary consultation features
- Integration with external veterinary practice management systems
- Prescription management or controlled substance tracking
- Billing or cost tracking for veterinary treatments (this may be added as a future enhancement to EPIC-7 reporting)
- Human patient records of any kind

---

## Stories

- **S01: Medical Record Schema** — Design and migrate the complete PostgreSQL schema for medical records, including the main records table, the vaccinations table with schedule fields, the medications table with active-status logic, and the file attachments table. Create the appropriate foreign key relationships to the animals table. Write Alembic migrations with rollback.

- **S02: Veterinary Notes & Documents** — Implement the staff and veterinarian-facing endpoints for creating, reading, and updating medical record entries. Support attaching files (PDFs, images) to individual records with validation of file type and size. Enforce access control so that only staff, veterinarian, and admin roles can create or edit records.

- **S03: Medical Timeline & History** — Implement the endpoint that returns the full chronological medical history for a specific animal. The response groups events by year and month for readability. Include aggregated summary fields (total recorded vet visits, date of last checkup, current active medications count, overdue vaccination count) to support the admin dashboard.

- **S04: Vaccination & Medication Tracking** — Implement the vaccination schedule endpoint that calculates overdue and upcoming vaccinations based on the due date fields in the vaccination records. Implement the active medications view that returns only records with a current date falling between the start and end dates. Emit notification events to EPIC-6 for upcoming vaccination reminders.

---

## Dependencies

**Depends on**:
- EPIC-1 (Animal Catalog & Management) — medical records are foreign-keyed to animal IDs; the medical hold status update touches the animal status field defined in EPIC-1
- EPIC-10 (Authentication & User Accounts) — read/write access to medical records requires authenticated users; read access is restricted to staff, veterinarian, and admin roles; the public health summary endpoint is unauthenticated
- EPIC-6 (Communications & Notifications) — vaccination reminders are delivered via EPIC-6's notification system; this epic emits the reminder events
- Object storage provisioning (EPIC-9, S03) — file attachments for lab reports and X-rays require a configured S3-compatible bucket

**Blocks**:
- EPIC-7 (Admin Dashboards) — aggregate health metrics (treatment costs, vaccination compliance rates, animals on medical hold) are displayed in the admin reporting view

---

## Success Metrics

- Staff can create a complete intake medical record for a newly arrived animal in under five minutes
- Overdue vaccinations are surfaced in the dashboard within 24 hours of the due date passing
- Zero medical record loss — all records are immutable once created; corrections are appended as new records
- The medical timeline for an animal with a two-year history loads in under 500 milliseconds
- Adopters receive a complete vaccination history with their adoption documentation via EPIC-2's contract

---

## Risk Factors

- **GDPR and animal data privacy**: While animals are not data subjects under GDPR, records may contain information about the people who surrendered them. Surrender reason notes and owner contact details should be treated with the same care as personal data. Mitigation: separate surrender records from medical records; apply PII exclusion rules from EPIC-9's logging configuration.
- **Schema complexity vs. flexibility**: Veterinary records vary widely. Overly rigid schema will frustrate vets; excessively flexible schema makes reporting impossible. Mitigation: use a structured base record with required fields and an optional JSONB field for extended clinical attributes that don't fit the standard structure.
- **File storage costs**: High-resolution X-rays and lab documents can be large. Mitigation: enforce a maximum file size at the API boundary and document the expected storage growth rate to inform hosting cost projections.

---

## Effort & Priority

**Priority**: Medium-high. Medical records are essential for legal compliance and quality of care but do not block the public-facing adoption flow. S01 (schema) and S04 (vaccination tracking) are the highest-value deliverables and should be prioritized.

**Estimated effort**: Two sprints. The schema and basic CRUD (S01, S02) form the first sprint. The timeline view and vaccination scheduling logic (S03, S04) follow in the second sprint.
