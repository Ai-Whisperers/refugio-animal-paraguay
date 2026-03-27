# RAP-147 Plan

## Objective
Create a prescription management view that lets staff see and track all active medication prescriptions across all animals.

## Description
The existing system records medications linked to treatments/diagnoses/vet visits. What was missing was a cross-animal view of all prescriptions. This story adds a `GET /prescriptions` API endpoint and a `/admin/prescriptions` frontend page.

## Acceptance Criteria
- [x] Staff can see all active prescriptions across all animals
- [x] Prescriptions show animal name, medication name, dosage, frequency, status
- [x] Status filter (active / completed / discontinued / all)
- [x] Link to animal's medical record from each prescription row
- [x] Backend: GET /prescriptions with pagination and filters

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple Fix — New read-only endpoint joining existing tables; frontend list page only.

## Approach
- Backend: New `prescriptions.py` router with a single GET endpoint joining medications → treatments → diagnoses → vet_visits → animals
- Frontend: New `/admin/prescriptions` page with status filter
- Sidebar navigation updated (added Recetas, Citas Medicas, Panel Veterinario)

## Dependencies
- Medication model (existing)
- Treatment/Diagnosis/VetVisit models (existing)
- Animal model (existing)
