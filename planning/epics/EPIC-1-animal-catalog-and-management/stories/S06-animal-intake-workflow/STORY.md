---
story: S06
epic: EPIC-1
title: Animal Intake Workflow
status: ready
created: 2026-03-26T00:00:00.000000
effort: 8
---

# S06: Animal Intake Workflow

## User Story

As a **staff member**, I want to **process new animals entering the shelter through a structured intake workflow capturing source, finder information, location, condition, and photos** so that **we have complete intake records for impact reporting, medical triaging, and inventory management**.

## Acceptance Criteria

**Given** a new animal arrives at the shelter
**When** staff initiates the intake process
**Then** the intake form is presented with source categorization (stray, surrender, rescue, transfer) and finder information fields

**Given** I am processing intake for a stray animal
**When** I complete the intake form
**Then** I can specify the location found, finder contact info, and condition on arrival

**Given** intake photos are being captured
**When** I upload before/after photos
**Then** the photos are linked to the animal record and available for impact reports

**Given** I indicate the animal requires quarantine
**When** I mark the health status as concerning
**Then** a medical record is automatically created in the medical system (EPIC-4) flagged for veterinary review

**Given** the intake workflow is complete
**When** I submit the form
**Then** the animal is added to the shelter inventory with status "intake-pending-assessment"

## Tasks

- T01: Create intake form schema and API endpoint (POST /animals/intake) with validation
- T02: Implement intake source categorization (enum: stray, surrender, rescue, transfer) with finder info schema
- T03: Integrate intake photo capture with existing photo gallery system, link photos to intake records
- T04: Create quarantine trigger logic that auto-creates medical record (EPIC-4 linkage) for concerning animals
- T05: Write unit and integration tests for intake workflow including edge cases and medical linkage

## Definition of Done

- [ ] Intake form schema validates all required fields (source, location/finder info, condition, photos)
- [ ] API endpoint accepts and stores intake records with proper data validation
- [ ] Source categorization (stray, surrender, rescue, transfer) is implemented and accessible
- [ ] Before/after photos are captured and linked to animal records
- [ ] Quarantine flag triggers automatic medical record creation in EPIC-4 system
- [ ] Animal status transitions correctly through intake workflow
- [ ] Unit tests cover form validation and data storage (80%+ coverage)
- [ ] Integration tests verify end-to-end intake workflow including medical linkage
- [ ] Staff role authorization is enforced at API level

## Technical Notes

- Intake model: id, animal_id, source (enum), finder_name, finder_email, finder_phone, location_found, condition_on_arrival (text), requires_quarantine (boolean), intake_date, staff_id, photos (FK to photos table), medical_record_id (optional FK to medical_records)
- Source enum: "stray", "surrender", "rescue", "transfer"
- Condition on arrival: free-form text field for initial observations
- Quarantine trigger: When requires_quarantine=true, automatically create medical record with status "pending-assessment"
- Photo integration: Use existing gallery system (EPIC-1), store relationship as intake_id → photo_ids
- Database indexes: animal_id, intake_date, source, requires_quarantine
- Authorization: staff role required for intake creation

## Dependencies

- Depends on: EPIC-10 (Authentication system for staff role), EPIC-1 (Animal model and photo system)
- Links to: EPIC-4 (Medical records system for quarantine medical record creation)

## Story Points: 8
